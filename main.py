#!/usr/bin/env python3
"""
Qwen-Agent — agente de desarrollo autónomo sobre qwen2.5-coder vía Ollama.

Uso:
    python main.py

Escribe tu orden cuando veas el indicador [Qwen-Agent-Ready]. Escribe
'salir' (o Ctrl+C) para terminar.
"""
from __future__ import annotations

import sys

# La consola de Windows (cmd/PowerShell) suele arrancar en cp1252, que no
# puede codificar los emojis usados en la salida y tumbaría el REPL con
# UnicodeEncodeError. Forzamos UTF-8 antes de imprimir nada.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.panel import Panel

import config
from agent.core import Agent
from agent.history import HistoryLogger
from agent.ollama_client import ModelUnavailableError, OllamaClient
from agent.skill_registry import load_skills, skills_to_prompt_block
from system_prompt import build_system_prompt


def main() -> None:
    console = Console()
    console.print(
        Panel.fit(
            "[bold cyan]⚡ QWEN-AGENT ⚡[/bold cyan]\n[dim]Agente de desarrollo autónomo · qwen2.5-coder vía Ollama[/dim]",
            border_style="cyan",
        )
    )

    console.print("[dim]Conectando con Ollama y verificando modelos disponibles...[/dim]")
    client = OllamaClient(config.OLLAMA_HOST, config.MODEL_CHAIN, config.REQUEST_TIMEOUT_SECONDS)
    try:
        model = client.ensure_model_available(
            on_fallback=lambda pref, actual: console.print(
                f"[yellow]⚠ '{pref}' no está descargado — usando '{actual}'.[/yellow]"
            )
        )
    except ModelUnavailableError as exc:
        console.print(f"[bold red]✗ {exc}[/bold red]")
        raise SystemExit(1)
    console.print(f"[green]✓ Modelo activo:[/green] {model}")

    registry = load_skills()
    console.print(f"[green]✓ Skills cargadas ({len(registry)}):[/green] " + ", ".join(registry))

    history = HistoryLogger(config.HISTORY_MD_FILE, config.HISTORY_JSONL_FILE)
    console.print(f"[green]✓ Bitácora:[/green] {config.HISTORY_MD_FILE.name}")

    system_prompt = build_system_prompt(
        model_name=model,
        skills_block=skills_to_prompt_block(registry),
        max_self_healing=config.MAX_SELF_HEALING_ATTEMPTS,
    )
    agent = Agent(client, registry, history, console)

    console.print()
    while True:
        try:
            console.print(r"[bold cyan]\[Qwen-Agent-Ready][/bold cyan] ⚡ Escribe tu orden: ", end="")
            instruction = input().strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Hasta luego.[/dim]")
            break

        if not instruction:
            continue
        if instruction.lower() in {"salir", "exit", "quit"}:
            console.print("[dim]Hasta luego.[/dim]")
            break

        console.rule(f"[bold]{instruction}[/bold]")
        agent.run_task(instruction, system_prompt)
        console.print()


if __name__ == "__main__":
    main()
