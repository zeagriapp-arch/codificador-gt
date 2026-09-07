"""
Skills de sistema de archivos: leer, escribir, listar y editar.

La edición usa bloques buscar/reemplazar (agent/diff_utils.py) en vez de
reescribir archivos completos: más barato en tokens y más seguro para
archivos ya existentes. La escritura completa se reserva para archivos
nuevos.
"""
from __future__ import annotations

from pathlib import Path

import config
from agent.diff_utils import SearchTextNotFound, apply_search_replace
from agent.skill_registry import Skill, SkillResult, register_skill

MAX_READ_CHARS = 20_000


def _resolve(path: str) -> Path:
    return (config.WORKDIR / path).resolve()


@register_skill
class WriteFileSkill(Skill):
    name = "escribir_archivo"
    description = "Crea un archivo nuevo (o sobrescribe uno) con el contenido dado. Úsala solo para archivos nuevos."
    parameters = {
        "path": "Ruta del archivo relativa a la raíz del proyecto.",
        "content": "Contenido completo del archivo.",
    }

    def run(self, path: str, content: str) -> SkillResult:
        target = _resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return SkillResult(success=True, output=f"Archivo '{path}' escrito ({len(content)} caracteres).")


@register_skill
class ReadFileSkill(Skill):
    name = "leer_archivo"
    description = "Lee y devuelve el contenido de un archivo existente."
    parameters = {"path": "Ruta del archivo relativa a la raíz del proyecto."}

    def run(self, path: str) -> SkillResult:
        target = _resolve(path)
        if not target.exists():
            return SkillResult(success=False, output=f"El archivo '{path}' no existe.")
        content = target.read_text(encoding="utf-8", errors="replace")
        truncated = content[:MAX_READ_CHARS]
        note = "" if len(content) <= MAX_READ_CHARS else f"\n[...truncado, {len(content)} caracteres en total...]"
        return SkillResult(success=True, output=truncated + note)


@register_skill
class ListDirSkill(Skill):
    name = "listar_directorio"
    description = "Lista archivos y carpetas dentro de una ruta (por defecto, la raíz del proyecto)."
    parameters = {"path": "Ruta relativa a listar. Opcional, por defecto '.'."}

    def run(self, path: str = ".") -> SkillResult:
        target = _resolve(path)
        if not target.exists():
            return SkillResult(success=False, output=f"La ruta '{path}' no existe.")
        entries = sorted(p.name + ("/" if p.is_dir() else "") for p in target.iterdir())
        return SkillResult(success=True, output="\n".join(entries) or "(directorio vacío)")


@register_skill
class EditFileSkill(Skill):
    name = "editar_archivo"
    description = (
        "Edita un archivo EXISTENTE reemplazando un bloque de texto exacto por otro "
        "(estilo buscar/reemplazar). Prefiérela sobre 'escribir_archivo' para archivos ya creados."
    )
    parameters = {
        "path": "Ruta del archivo a editar.",
        "search": "Texto exacto a buscar (incluye indentación tal cual aparece en el archivo).",
        "replace": "Texto que reemplazará al buscado.",
    }

    def run(self, path: str, search: str, replace: str) -> SkillResult:
        target = _resolve(path)
        if not target.exists():
            return SkillResult(success=False, output=f"El archivo '{path}' no existe.")
        try:
            apply_search_replace(target, search, replace)
        except SearchTextNotFound as exc:
            return SkillResult(success=False, output=str(exc))
        return SkillResult(success=True, output=f"Archivo '{path}' editado correctamente.")
