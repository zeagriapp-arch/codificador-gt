"""
Skill de Git: respalda con un commit automático cada avance exitoso.

Si la carpeta todavía no es un repositorio, lo inicializa sola la primera
vez que se usa — coherente con "100% autónomo, sin pedir nada".
"""
from __future__ import annotations

import subprocess

import config
from agent.skill_registry import Skill, SkillResult, register_skill


def _run(command: str) -> subprocess.CompletedProcess:
    return subprocess.run(command, shell=True, cwd=config.WORKDIR, capture_output=True, text=True)


@register_skill
class GitCommitSkill(Skill):
    name = "git_commit"
    description = (
        "Guarda el estado actual del proyecto con un commit de git. Si la carpeta todavía "
        "no es un repositorio, lo inicializa primero. Úsala al concluir con éxito una tarea "
        "o un paso importante."
    )
    parameters = {"message": "Mensaje del commit, breve y descriptivo."}

    def run(self, message: str) -> SkillResult:
        if not (config.WORKDIR / ".git").exists():
            init = _run("git init")
            if init.returncode != 0:
                return SkillResult(success=False, output=f"No se pudo inicializar git: {init.stderr}")

        _run("git add -A")
        commit = _run(f'git commit -m "{message}"')
        if commit.returncode != 0:
            combined = (commit.stdout + commit.stderr).lower()
            if "nothing to commit" in combined:
                return SkillResult(success=True, output="No había cambios pendientes por commitear.")
            return SkillResult(success=False, output=f"Falló el commit: {commit.stdout}\n{commit.stderr}")

        return SkillResult(success=True, output=f'Commit realizado: "{message}"')
