"""
Edición de archivos por bloques buscar/reemplazar.

El LLM produce dos textos (search, replace) en action_input para la skill
'editar_archivo'. Es más barato en tokens y más seguro que pedirle que
reescriba el archivo completo: solo toca lo que necesita tocar.
"""
from __future__ import annotations

from pathlib import Path


class SearchTextNotFound(ValueError):
    pass


def apply_search_replace(file_path: Path, search: str, replace: str) -> str:
    """Reemplaza la primera ocurrencia exacta de `search` por `replace`."""
    original = file_path.read_text(encoding="utf-8")
    if search not in original:
        raise SearchTextNotFound(
            "El texto buscado no aparece exactamente en el archivo. "
            "Vuelve a leerlo con 'leer_archivo' y revisa espacios/indentación antes de reintentar."
        )
    updated = original.replace(search, replace, 1)
    file_path.write_text(updated, encoding="utf-8")
    return updated
