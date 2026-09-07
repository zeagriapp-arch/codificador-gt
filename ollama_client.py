"""
Cliente de Ollama con fallback automático de modelo.

Si el modelo preferido no está disponible (no descargado, timeout, error del
servidor por falta de VRAM), el cliente degrada al siguiente modelo de la
cadena configurada en config.py sin que el REPL se caiga.
"""
from __future__ import annotations

from typing import Callable

import requests

OnFallback = Callable[[str, str], None]


class ModelUnavailableError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, host: str, model_chain: list[str], timeout: int):
        self.host = host.rstrip("/")
        self.model_chain = model_chain
        self.timeout = timeout
        self.current_model: str | None = None

    def _installed_models(self) -> set[str]:
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=10)
            resp.raise_for_status()
            return {m["name"] for m in resp.json().get("models", [])}
        except requests.RequestException as exc:
            raise ModelUnavailableError(
                f"No se pudo conectar con Ollama en {self.host}. "
                f"¿Está corriendo 'ollama serve'? Detalle: {exc}"
            ) from exc

    def ensure_model_available(self, on_fallback: OnFallback | None = None) -> str:
        """Elige el primer modelo de la cadena que esté descargado en Ollama."""
        installed = self._installed_models()
        for i, model in enumerate(self.model_chain):
            if model in installed:
                if i > 0 and on_fallback:
                    on_fallback(self.model_chain[0], model)
                self.current_model = model
                return model
        raise ModelUnavailableError(
            "Ninguno de los modelos configurados está descargado en Ollama.\n"
            "Instala al menos uno, por ejemplo:\n"
            f"  ollama pull {self.model_chain[-1]}"
        )

    def chat(self, messages: list[dict[str, str]], on_fallback: OnFallback | None = None) -> str:
        """Envía la conversación al modelo activo; si falla, degrada al siguiente."""
        if self.current_model is None:
            self.ensure_model_available(on_fallback)

        start_index = self.model_chain.index(self.current_model)
        last_error: Exception | None = None

        for model in self.model_chain[start_index:]:
            try:
                resp = requests.post(
                    f"{self.host}/api/chat",
                    json={"model": model, "messages": messages, "stream": False},
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                content = resp.json()["message"]["content"]
                if model != self.current_model and on_fallback:
                    on_fallback(self.current_model, model)
                self.current_model = model
                return content
            except (requests.RequestException, KeyError, ValueError) as exc:
                last_error = exc
                continue

        raise ModelUnavailableError(f"Todos los modelos de la cadena fallaron. Último error: {last_error}")
