"""
Registro de Skills: arquitectura de plugins.

Cada skill vive en su propio archivo dentro de skills/ y se registra a sí
misma con el decorador @register_skill. Para agregar una habilidad nueva al
agente basta con crear un archivo ahí — nada del core necesita tocarse, y el
system prompt se actualiza solo porque la lista de skills se genera en
tiempo de ejecución a partir de este registro.
"""
from __future__ import annotations

import importlib
import pkgutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillResult:
    """Resultado uniforme que devuelve cualquier skill."""

    success: bool
    output: str
    data: dict[str, Any] = field(default_factory=dict)


class Skill(ABC):
    """Contrato que toda skill debe cumplir."""

    name: str
    description: str
    # nombre de parámetro -> descripción en lenguaje natural para el LLM.
    parameters: dict[str, str] = {}

    @abstractmethod
    def run(self, **kwargs: Any) -> SkillResult:
        ...

    def prompt_block(self) -> str:
        params = ", ".join(f"{k} ({v})" for k, v in self.parameters.items()) or "sin parámetros"
        return f"- {self.name}: {self.description}\n  Parámetros: {params}"


SKILL_REGISTRY: dict[str, Skill] = {}


def register_skill(cls: type[Skill]) -> type[Skill]:
    """Decorador: instancia la skill y la agrega al registro global."""
    instance = cls()
    if instance.name in SKILL_REGISTRY:
        raise ValueError(f"Skill duplicada: '{instance.name}' ya está registrada.")
    SKILL_REGISTRY[instance.name] = instance
    return cls


def load_skills(package: str = "skills") -> dict[str, Skill]:
    """Importa todos los módulos de skills/ para que se auto-registren."""
    pkg = importlib.import_module(package)
    for _, module_name, _ in pkgutil.iter_modules(pkg.__path__, prefix=f"{package}."):
        importlib.import_module(module_name)
    return SKILL_REGISTRY


def skills_to_prompt_block(registry: dict[str, Skill]) -> str:
    return "\n".join(skill.prompt_block() for skill in registry.values())
