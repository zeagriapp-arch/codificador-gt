"""
Núcleo del agente: bucle ReAct (Razona -> Actúa -> Observa) con
autocorrección integrada.

Cada instrucción del usuario dispara un ciclo donde el modelo:
  1. Piensa y elige UNA skill a ejecutar (respuesta en JSON).
  2. El core ejecuta esa skill y le devuelve el resultado como observación.
  3. El modelo decide el siguiente paso, hasta responder "finish".

Si una skill falla, el error se retroalimenta como observación: el propio
modelo la diagnostica y la corrige en el siguiente paso (autocorrección),
hasta un límite de fallos consecutivos definido en config.py.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

from rich.console import Console

import config
from agent.history import HistoryLogger
from agent.ollama_client import OllamaClient
from agent.skill_registry import Skill, SkillResult


class MalformedResponseError(ValueError):
    pass


def _extract_json(text: str) -> dict[str, Any]:
    """Extrae el primer objeto JSON de la respuesta del modelo, tolerando que
    lo envuelva en ```json ... ``` o le agregue texto alrededor (los modelos
    locales no siempre respetan el formato al pie de la letra)."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()

    start = text.find("{")
    if start == -1:
        raise MalformedResponseError("La respuesta no contiene un objeto JSON.")

    depth = 0
    for i, ch in enumerate(text[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise MalformedResponseError("El objeto JSON de la respuesta está incompleto.")


class Agent:
    def __init__(self, client: OllamaClient, registry: dict[str, Skill], history: HistoryLogger, console: Console):
        self.client = client
        self.registry = registry
        self.history = history
        self.console = console

    def _on_fallback(self, old: str, new: str) -> None:
        self.console.print(f"[yellow]⚠ '{old}' no disponible/falló — degradando a '{new}'.[/yellow]")
        self.history.log_markdown(f"⚠ Fallback de modelo: {old} → {new}")

    def run_task(self, instruction: str, system_prompt: str) -> None:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction},
        ]
        self.history.log_markdown(f"**Orden recibida:** {instruction}")

        consecutive_failures = 0
        malformed_responses = 0

        for step in range(1, config.MAX_AGENT_ITERATIONS + 1):
            with self.console.status(f"[bold cyan]Pensando (paso {step})...[/bold cyan]"):
                t0 = time.time()
                raw = self.client.chat(messages, on_fallback=self._on_fallback)
                latency = time.time() - t0

            self.history.log_jsonl(
                {"step": step, "model": self.client.current_model, "latency_s": round(latency, 2), "response": raw}
            )

            try:
                action = _extract_json(raw)
            except MalformedResponseError as exc:
                malformed_responses += 1
                self.console.print(f"[red]✗ Respuesta no interpretable: {exc}[/red]")
                if malformed_responses >= config.MAX_MALFORMED_RESPONSES:
                    self.console.print("[bold red]Demasiadas respuestas mal formadas. Abortando tarea.[/bold red]")
                    return
                messages.append({"role": "assistant", "content": raw})
                messages.append(
                    {
                        "role": "user",
                        "content": f"Tu respuesta no es JSON válido ({exc}). "
                        f"Responde ÚNICAMENTE con el objeto JSON indicado en las reglas.",
                    }
                )
                continue

            malformed_responses = 0
            messages.append({"role": "assistant", "content": raw})

            thought = action.get("thought", "")
            act_name = action.get("action")
            act_input = action.get("action_input") or {}

            if thought:
                self.console.print(f"[dim]💭 {thought}[/dim]")

            if act_name == "finish":
                final_message = act_input.get("message", "Tarea completada.")
                self.console.print(f"[bold green]✅ {final_message}[/bold green]")
                self.history.log_markdown(f"**Resultado:** {final_message}")
                return

            skill = self.registry.get(act_name)
            if skill is None:
                observation = f"Skill '{act_name}' no existe. Skills disponibles: {', '.join(self.registry)}"
                consecutive_failures += 1
            else:
                self.console.print(f"[cyan]🔧 {act_name}[/cyan]({act_input})")
                try:
                    result: SkillResult = skill.run(**act_input)
                except Exception as exc:  # una skill jamás debe tumbar el REPL
                    result = SkillResult(success=False, output=f"Excepción no controlada: {exc}")

                status = "[green]✓[/green]" if result.success else "[red]✗[/red]"
                self.console.print(f"  {status} {result.output[:500]}")
                self.history.log_markdown(
                    f"- Skill `{act_name}` ({'ok' if result.success else 'error'}): {result.output[:1000]}"
                )
                observation = result.output
                consecutive_failures = 0 if result.success else consecutive_failures + 1

            if consecutive_failures >= config.MAX_SELF_HEALING_ATTEMPTS:
                msg = (
                    f"Se alcanzó el límite de {config.MAX_SELF_HEALING_ATTEMPTS} intentos de "
                    f"autocorrección consecutivos. Deteniendo la tarea."
                )
                self.console.print(f"[bold red]🛑 {msg}[/bold red]")
                self.history.log_markdown(f"**Abortado:** {msg}")
                return

            messages.append({"role": "user", "content": f"Observación: {observation}"})

        self.console.print("[bold yellow]⏱ Se alcanzó el límite de pasos para esta orden.[/bold yellow]")
