"""
Configuración central del agente.

Todo lo que pueda variar entre entornos (modelo, timeouts, límites) vive
aquí, para no tener que tocar el código de las skills ni del core cuando
cambias algo.
"""
from __future__ import annotations

import os
from pathlib import Path

# --- Ollama ---
OLLAMA_HOST: str = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# Cadena de modelos: el agente intenta el primero; si Ollama no lo tiene
# descargado, o una llamada falla (timeout, sin VRAM suficiente, etc.),
# degrada automáticamente al siguiente sin tumbar el REPL.
MODEL_CHAIN: list[str] = [
    "qwen2.5-coder:72b",
    "qwen2.5-coder:32b",
    "qwen2.5-coder:14b",
]

REQUEST_TIMEOUT_SECONDS: int = 300  # margen amplio: 72b puede tardar en generar

# --- Directorio de trabajo ---
# El agente opera siempre sobre la raíz del proyecto donde se lanza, sin
# anidar estructuras propias complicadas.
WORKDIR: Path = Path.cwd()

# --- Ejecución de comandos ---
# Sin lista negra ni confirmaciones: el agente tiene autonomía total sobre
# el shell, por decisión explícita de configuración. El único límite es de
# tiempo, para que un proceso colgado no deje la sesión congelada.
COMMAND_TIMEOUT_SECONDS: int = 120

# --- Bucle de razonamiento (ReAct) ---
MAX_AGENT_ITERATIONS: int = 30       # pasos máximos por orden del usuario
MAX_SELF_HEALING_ATTEMPTS: int = 5   # fallos consecutivos antes de abortar la tarea
MAX_MALFORMED_RESPONSES: int = 3     # respuestas no-JSON consecutivas antes de abortar

# --- Bitácora ---
HISTORY_MD_FILE: Path = WORKDIR / "historial_agente.md"
HISTORY_JSONL_FILE: Path = WORKDIR / "agent_log.jsonl"
