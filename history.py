"""
Bitácora del agente: un log legible para humanos (historial_agente.md) y uno
estructurado (agent_log.jsonl) para depurar al agente mismo — qué prompt
recibió, qué respondió, cuánto tardó, qué modelo lo atendió.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class HistoryLogger:
    def __init__(self, md_path: Path, jsonl_path: Path):
        self.md_path = md_path
        self.jsonl_path = jsonl_path
        if not self.md_path.exists():
            self.md_path.write_text(
                "# Historial del Agente\n\nBitácora automática de cada orden y acción ejecutada.\n\n",
                encoding="utf-8",
            )

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def log_markdown(self, entry: str) -> None:
        with self.md_path.open("a", encoding="utf-8") as f:
            f.write(f"### {self._timestamp()}\n{entry}\n\n")

    def log_jsonl(self, record: dict[str, Any]) -> None:
        record = {"timestamp": self._timestamp(), **record}
        with self.jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
