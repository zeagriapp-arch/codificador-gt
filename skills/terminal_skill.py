"""
Skill de terminal: ejecuta comandos de shell directamente sobre el sistema.

Sin lista negra ni confirmaciones — el agente opera con autonomía total
sobre el shell, por decisión explícita de configuración. Úsalo en un
entorno del que puedas permitirte perder datos (ideal: una VM o contenedor
descartable), no directamente sobre una máquina de producción.
"""
from __future__ import annotations

import subprocess

import config
from agent.skill_registry import Skill, SkillResult, register_skill


@register_skill
class TerminalSkill(Skill):
    name = "ejecutar_terminal"
    description = (
        "Ejecuta un comando de shell en el directorio de trabajo y devuelve stdout, "
        "stderr y el código de salida. Úsalo para instalar dependencias, correr "
        "scripts, crear entornos virtuales, o cualquier operación de sistema."
    )
    parameters = {"command": "Comando de shell a ejecutar, como string."}

    def run(self, command: str) -> SkillResult:
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
            return SkillResult(
                success=False,
                output=f"El comando excedió {config.COMMAND_TIMEOUT_SECONDS}s y fue terminado.",
            )

        output = f"exit_code={proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        return SkillResult(success=proc.returncode == 0, output=output)
