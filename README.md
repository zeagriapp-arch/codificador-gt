# Qwen-Agent

Agente de desarrollo autónomo sobre **qwen2.5-coder** (vía [Ollama](https://ollama.com)), con arquitectura de Skills en plugins, edición de código por bloques buscar/reemplazar, autocorrección con pruebas reales y commits automáticos.

## ⚠️ Antes de correrlo

Este agente ejecuta comandos de shell **sin ninguna restricción ni confirmación** (`skills/terminal_skill.py`): puede instalar paquetes, borrar archivos, hacer commits, lo que decida que necesita hacer para resolver tu orden. Es autonomía total por diseño. Recomendado:

- Córrelo dentro de una carpeta de proyecto dedicada (no en `/`, tu `$HOME` completo, etc.).
- Si vas a darle tareas de las que no quieres depender, hazlo en una instancia o contenedor descartable (por ejemplo, una instancia de [Vast.ai](https://vast.ai) dedicada a este agente).

## Requisitos

1. [Ollama](https://ollama.com) instalado y corriendo. En una instancia Linux (Vast.ai u otra):
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama serve &
   ```
2. Al menos uno de estos modelos descargado (el agente usa el primero disponible, en este orden):
   ```bash
   ollama pull qwen2.5-coder:72b
   ollama pull qwen2.5-coder:32b
   ollama pull qwen2.5-coder:14b
   ```
3. Python 3.10+ (`python3 --version`).

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python3 main.py
```

Cuando veas `[Qwen-Agent-Ready] ⚡ Escribe tu orden:`, todo está conectado y listo. Escribe tu instrucción en lenguaje natural y el agente planea, ejecuta y se autocorrige hasta resolverla. Escribe `salir` para terminar.

## Arquitectura

```
main.py               REPL: banner, arranque, bucle de entrada
config.py             toda la configuración (modelo, timeouts, límites)
system_prompt.py      reglas del agente + formato de acción obligatorio
agent/
  core.py             bucle ReAct (pensar → actuar → observar) + autocorrección
  ollama_client.py     cliente de Ollama con fallback automático de modelo
  skill_registry.py    registro de Skills tipo plugin (auto-descubrimiento)
  diff_utils.py        aplica ediciones buscar/reemplazar sobre archivos
  history.py           historial_agente.md + agent_log.jsonl
skills/                cada archivo aquí es una Skill que se auto-registra
  terminal_skill.py     ejecutar_terminal
  filesystem_skill.py   escribir_archivo, leer_archivo, listar_directorio, editar_archivo
  test_skill.py         correr_tests (pytest)
  git_skill.py          git_commit
```

### Cómo decide el agente qué hacer

En cada paso, el modelo responde con un único JSON:

```json
{"thought": "razonamiento breve", "action": "nombre_de_skill", "action_input": {...}}
```

El core ejecuta esa skill, le devuelve el resultado como "Observación", y el modelo decide el siguiente paso — hasta responder con `"action": "finish"`. Si una skill falla, el propio modelo ve el error en la observación y lo corrige en el siguiente paso; tras 5 fallos consecutivos, la tarea se aborta y se reporta con claridad en vez de quedar en un loop infinito.

### Agregar una Skill nueva

Crea un archivo en `skills/`, define una clase que herede de `Skill` (en `agent/skill_registry.py`) y decórala con `@register_skill`:

```python
from agent.skill_registry import Skill, SkillResult, register_skill

@register_skill
class MiSkill(Skill):
    name = "mi_skill"
    description = "Qué hace, en una línea clara para el modelo."
    parameters = {"param": "qué es este parámetro"}

    def run(self, param: str) -> SkillResult:
        return SkillResult(success=True, output="listo")
```

No necesitas tocar `main.py` ni `system_prompt.py`: se auto-descubre y aparece en las skills disponibles del modelo en el siguiente arranque.

## Bitácora

- `historial_agente.md` — registro legible de cada orden y acción.
- `agent_log.jsonl` — registro estructurado (modelo usado, latencia, respuesta cruda) para depurar al propio agente.

Ambos se generan en la raíz del proyecto la primera vez que corres el agente.
