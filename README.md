# DesviAI

Sistema de **predicción y diagnóstico de desvío de costos y plazos** en obras de
construcción (TFM · IA aplicada al sector AECO).

Un modelo predictivo cerrado (**Random Forest + SHAP**, 200 obras) estima el desvío de
costo y de plazo y clasifica el riesgo. Sobre él se construye una capa de **diagnóstico**:
explica *por qué* una obra se desvía, *qué se hizo bien/mal* y *qué aprender*, mediante un
**agente conversacional** con *tool calling* que cita cada afirmación a su fuente. La base
de conocimiento es un esquema de archivos `.md` (memoria **semántica / procedural /
episódica**), sin RAG.

## Opción rápida: Docker (sin instalar Python)

Para **probar el prototipo sin configurar nada** (ideal para revisores):

```
docker compose up --build     # abrir http://localhost:8200
```

La primera vez tarda unos minutos (instala todo y entrena el modelo dentro del contenedor).
Guía detallada para el revisor en [`docs/PROBAR_CON_DOCKER.md`](docs/PROBAR_CON_DOCKER.md).

## Puesta en marcha para desarrollo (después de clonar)

Requisitos: **Python 3.12+** y **git**. En Windows (PowerShell):

```powershell
cd DESVIAI_TFM/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Genera los artefactos del modelo (reproduce el notebook, ~1 min)
python core/ml/train.py

# (Opcional) regenera la memoria episódica y las órdenes de cambio
python core/ml/gen_memoria.py

# Levanta la app (UI + API en el mismo servidor)
python manage.py runserver 127.0.0.1:8200
```

En macOS/Linux, activar el venv con `source .venv/bin/activate`.

Luego abrir en el navegador:

- **App**: http://127.0.0.1:8200/
- **Diagrama de arquitectura**: http://127.0.0.1:8200/arquitectura.html
- **Estado de la API**: http://127.0.0.1:8200/api/health

> Los artefactos del modelo (`backend/core/ml/artifacts/*.pkl`) **no** están en el repo
> (se regeneran con `train.py`), así que ese paso es obligatorio la primera vez.

## Estructura del repo

```
DESVIAI_TFM/
├── README.md              este archivo
├── PLAN.md                plan del PoC/MVP y decisiones de diseño
├── arquitectura.html      diagrama de arquitectura (1 página)
├── DesviAI.html + *.jsx   interfaz web (React vía Babel, sin build)
├── styles.css
├── docs/
│   └── GUION_DEMO.md      guion para la presentación
├── presentacion/grafos/   grafos de las 3 memorias para la presentación final
│                          (vistas 1-3 + red interactiva tipo Obsidian + PNG 4K)
├── knowledge/             base de conocimiento (memorias .md, esquema OKF)
│   ├── semantica/         conceptos del dominio
│   ├── procedural/        guías de mitigación
│   └── episodica/         un episodio por obra cerrada
└── backend/               Django (API + sirve la UI)
    ├── README.md          detalle de endpoints y módulos
    ├── requirements.txt
    ├── config/            settings, urls
    ├── core/
    │   ├── ml/            modelo: train, predictor, explainer, contexto, similares (agente)…
    │   ├── agent/         agente conversacional (tools, mock, loop Claude)
    │   ├── memory.py      lectura de la base de conocimiento .md
    │   └── views_api.py   endpoints JSON
    └── eval/              evaluación del agente (5 casos canónicos)
```

Ver [`backend/README.md`](backend/README.md) para el detalle de los endpoints, las
métricas del modelo y el análisis de contexto de gestión.

📖 **¿Nuevo en el proyecto?** Empieza por [`docs/GUIA_DEL_PROYECTO.md`](docs/GUIA_DEL_PROYECTO.md)
— explica qué es, cómo funciona y qué hay en cada carpeta, en lenguaje sencillo.

## El agente con LLM (opcional) — Claude u OpenAI

Por defecto el agente corre en modo **`mock`** (determinístico, sin API key). Para usar un
LLM real, crear `backend/.env` a partir de `backend/.env.example`. **Claude y OpenAI son
alternativas intercambiables** (mismas herramientas, mismo prompt); se elige con `AGENT_MODE`:

```
# Opción A — Anthropic (Claude)
AGENT_MODE=claude
ANTHROPIC_API_KEY=sk-ant-...

# Opción B — OpenAI (GPT)
AGENT_MODE=openai
OPENAI_API_KEY=sk-...
```

El mismo interruptor rige la explicación del riesgo de gestión (botón "Explicar este riesgo"
en el reporte). Si el modo real no tiene su key, cae automáticamente a `mock`.

## Cómo colaborar

El proyecto está en `main`. Para trabajar en equipo sin pisarse:

```bash
git checkout -b mi-rama          # una rama por tarea/persona
# ...cambios...
git add -A && git commit -m "descripción"
git push -u origin mi-rama       # y abrir un Pull Request en GitHub
```

Evitar commitear el `.venv`, la base de datos ni los artefactos `.pkl` (ya están en
`.gitignore`).

## Créditos y trazabilidad

- El **modelo predictivo** (Random Forest + SHAP, notebook `construccion_predictivo.ipynb`)
  y el **dataset** de 200 obras son trabajo previo del equipo; el backend los empaqueta
  fielmente (las métricas coinciden con las del notebook).
- La **capa de diagnóstico** (memorias `.md`, análisis de contexto de gestión, agente con tool
  calling, evaluación y la conexión de la UI) es el aporte del PoC.

## Licencia

Este proyecto se distribuye bajo la licencia **MIT** — ver [`LICENSE`](LICENSE).
