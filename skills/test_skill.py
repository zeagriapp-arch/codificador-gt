"""
Skill de pruebas: corre pytest y devuelve el resultado real.

Cierra el ciclo de autocorrección con evidencia concreta — que el código
"no truene" no significa que funcione; que las pruebas pasen, sí.
"""
from __future__ import annotations

import subprocess

import config
from agent.skill_registry import Skill, SkillResult, register_skill


@register_skill
class RunTestsSkill(Skill):
    name = "correr_tests"
    description = (
        "Ejecuta la suite de pruebas (pytest) del proyecto y devuelve el resultado. "
        "Úsala después de escribir o modificar código para verificar que funciona de verdad, "
        "no solo que no truena."
    )
    parameters = {"args": "Argumentos extra para pytest, ej. una ruta específica. Opcional."}

    def run(self, args: str = "") -> SkillResult:
        command = f"python -m pytest {args}".strip()
        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=config.WORKDIR,
                capture_output=True,
                text=True,
                timeout=config.COMMAND_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return SkillResult(success=False, output="Las pruebas excedieron el tiempo límite y fueron terminadas.")

        output = proc.stdout[-4000:] + "\n" + proc.stderr[-2000:]
        return SkillResult(success=proc.returncode == 0, output=output)
