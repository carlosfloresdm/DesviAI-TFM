# DesviAI · Backend (PoC)

Backend Django que sirve el modelo predictivo (Random Forest + SHAP) y, en fases
posteriores, la base de conocimiento y el agente conversacional.

## Interfaz web (UI DesviAI)

Django sirve la UI React (raíz del repo) en el **mismo origen** que la API, así que no
hay CORS. Con el servidor arriba, abrir **http://127.0.0.1:8200/**. Flujo conectado al
modelo real: login → dashboard (cartera real de 200 obras) → formulario (10 campos del
modelo) → pipeline → **reporte** (predicción, banda, IC80%, SHAP, similares, desglose del
score contextual) → **chat** con el agente (tool calling con traza visible).

El dashboard y el historial consumen `/api/historico` (datos reales). Al hacer clic en una
obra del histórico se abre su **reporte real**; si tiene episodio, aparece la tarjeta de
**evidencia directa** y el agente cita sus órdenes de cambio.

- **Diagrama de arquitectura** (1 página): http://127.0.0.1:8200/arquitectura.html
- **Guion de demo**: [`docs/GUION_DEMO.md`](../docs/GUION_DEMO.md)

## Puesta en marcha

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate            # Windows PowerShell:  .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1) Entrenar y exportar artefactos (reproduce el notebook, ~1 min)
python core/ml/train.py

# 2) Generar órdenes de cambio sintéticas + memoria episódica (.md)
python core/ml/gen_memoria.py

# 3) Levantar la API
python manage.py runserver 127.0.0.1:8200
```

## Endpoints (Fase PoC)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/health` | Estado + resumen de métricas + conteo de memorias |
| GET | `/api/metrics` | Métricas de CV completas (`metrics.json`) |
| GET | `/api/shap-global` | Ranking SHAP global por target |
| POST | `/api/predict` | Desvío + banda de riesgo + IC80% (costo y tiempo) |
| POST | `/api/explain` | Descomposición SHAP local + resumen en lenguaje natural |
| POST | `/api/similares` | k proyectos comparables + desempeño real |
| POST | `/api/score-contextual` | Score de riesgo contextual (modelo + vecinos + episódica) |
| GET/POST | `/api/contexto/config` | Preguntas del checklist de contexto de gestión (+ pre-selección si se envía `{project}`) |
| POST | `/api/contexto/calcular` | Índice de riesgo de contexto de gestión a partir de `{checklist}` |
| POST | `/api/contexto/explicar` | Explicación en lenguaje natural del índice ya calculado (capa interpretativa, mock/claude/openai) |
| GET | `/api/atribucion` | Tabla de atribución agregada por causa (capa 3, estudio piloto) |
| GET | `/api/episodio/<id>` | Episodio de una obra (memoria episódica), si existe evidencia |
| POST | `/api/agent/chat` | Agente conversacional (capa 6): respuesta + traza de tools |

### Contrato de entrada (cuerpo POST)

```json
{
  "sup_m2": 45000, "niveles": 35, "unidades": 400,
  "presupuesto_inicial": 30000000, "tiempo_inicial": 730,
  "sistema_constructivo": "Concreto Postensado",
  "nivel_acabado": "Medio", "avance_proyecto": "70 - 80",
  "proyectos_similares": "10 - 15", "fecha_inicio": "2024-03"
}
```

Se admite el dict directo o envuelto en `{"project": {...}}`. `/api/explain` acepta
`"target": "desvio_costo" | "desvio_tiempo"` (por defecto ambos); `/api/similares`
acepta `"k"` y `"excluir_id"`.

## Estructura

```
backend/
├── manage.py
├── requirements.txt
├── config/            settings, urls, wsgi
└── core/
    ├── views_api.py   endpoints JSON
    ├── urls.py
    ├── ml/
    │   ├── features.py        ingeniería de variables (train == serve)
    │   ├── train.py           entrena y exporta artefactos
    │   ├── predictor.py       predicción + banda + IC80%
    │   ├── explainer.py       SHAP local/global
    │   ├── similares.py       kNN casos comparables
    │   ├── artifacts_meta.py  acceso cacheado a métricas/meta
    │   └── artifacts/         .pkl + .json generados por train.py
    └── data/
        └── dataset_construccion.xlsx
```

## Base de conocimiento (memorias .md)

Esquema OKF (sin RAG): archivos Markdown relacionados por front-matter y wikilinks,
en `../knowledge/` (raíz del repo). Tres memorias, según el feedback del mentor:

```
knowledge/
├── semantica/    conceptos del dominio (causas, tipologías, bandas, variables)
├── procedural/   procedimientos de mitigación por causa + checklist de arranque
├── episodica/    un episodio por obra cerrada (órdenes de cambio + lección)
└── atribucion_agregada.json   tabla de atribución de la capa 3 (estudio piloto)
```

`core/memory.py` lee estos .md (parsea front-matter, resuelve wikilinks) y los indexa
en caché. Tras regenerar la memoria episódica, reiniciar el servidor o llamar
`memory.reload()`.

## Score de riesgo contextual

`score = 100 × (0.5·prob_modelo + 0.3·tasa_vecinos + 0.2·señal_episódica)`

Determinístico y auditable: cada componente es citable por separado. Si los vecinos
tienen episodio documentado, la señal episódica usa **evidencia directa**; si no, cae a
la tasa de vecinos (**evidencia estadística**, declarada). El LLM narra el score, no lo
calcula.

## Análisis de contexto de gestión (checklist opcional)

Segunda lectura de riesgo, **paralela** al modelo y al score contextual (no los
modifica): evalúa el **contexto de gestión** que las dimensiones de diseño no
capturan (madurez del ejecutivo, permisos, terreno, contrato, cliente). Aporte del
equipo (plataforma "predictor_obras"), integrado en `core/ml/contexto.py`.

- **Checklist de 8 tipos de riesgo**: el usuario responde preguntas concretas (no
  niveles abstractos); cada opción tiene un peso normalizado [0,1] oculto.
- **Fórmula ancla determinística**: los 6 tipos base promedian (escala 0-2), el
  tipo 8 (equipo/cliente) **multiplica** (factor 0.8-1.3) y el tipo 7 (señales en
  ejecución) queda diferido hasta que exista bitácora de obra.
- Pre-selección desde datos ya cargados (`avance_proyecto` → madurez); el usuario
  siempre puede corregirla.
- **Capa interpretativa** (`core/agent/asistente.py`, endpoint `/api/contexto/explicar`):
  narra el índice ya calculado apoyándose en las notas `contexto-*` de
  `knowledge/semantica/` y sus procedurales de mitigación (vía wikilinks). **No
  recalcula el número.** En modo `mock` usa una plantilla determinística (la demo
  funciona sin API key); con `claude` u `openai` lo redacta el LLM real. En la UI es
  el botón "Explicar este riesgo" de la tarjeta de resultado.

Validación: `python eval/eval_contexto.py` corre los 5 casos canónicos de la
fórmula (piso, dilución, base alta, amplificador, techo).

## Agente conversacional (capa 6)

Agente con **tool calling** sobre las 4 herramientas (`consultar_shap`,
`buscar_episodio`, `buscar_casos_similares`, `leer_memoria`). Su única decisión
autónoma es **binaria y auditable**: si la obra tiene episodio documentado, cita las
órdenes de cambio (evidencia directa); si no, usa casos similares + inferencia agregada,
declarándolo. Cada respuesta incluye la **traza** de tools invocadas.

Tres modos (variable `AGENT_MODE`) — **Claude y OpenAI son alternativas
intercambiables**: mismas 4 tools, mismo prompt, mismo contrato de salida; solo
cambia el proveedor del LLM. Si el modo real no tiene su key, cae automáticamente a
`mock`:
- `mock` (por defecto) — respuestas determinísticas por plantilla, alimentadas por los
  datos reales de las tools. No requiere API key; la demo y la evaluación son reproducibles.
- `claude` — API de Anthropic (`ANTHROPIC_API_KEY`, modelo `AGENT_MODEL`), SDK nativo
  `anthropic` con tool calling (`core/agent/claude_loop.py`).
- `openai` — API de OpenAI (`OPENAI_API_KEY`, modelo `OPENAI_MODEL`), SDK nativo
  `openai` con function calling (`core/agent/openai_loop.py`). El esquema de las tools
  se traduce del formato Anthropic al de OpenAI.

Petición: `POST /api/agent/chat` con `{project, obra_id?, pregunta, historial?}`.

```
core/agent/
├── tools.py        4 tools + esquema Anthropic + prompt de sistema
├── mock.py         agente determinístico (clasifica intención → tools → plantilla)
├── claude_loop.py  loop de tool calling real (Anthropic)
├── openai_loop.py  loop de function calling real (OpenAI) — alternativa a Claude
├── llm.py          completado simple agnóstico de proveedor (para la capa interpretativa)
├── asistente.py    capa interpretativa: explica el índice de gestión con memoria
└── service.py      dispatcher mock/claude/openai
```

## Evaluación del agente (5 casos canónicos)

Exigencia del mentor: evaluar el agente con métricas. `eval/run_eval.py` corre 5 casos
canónicos y comprueba, contra la **verdad de referencia derivada de los datos** (no
valores fijados a mano), que el agente invoque las tools correctas, cite los números
exactos, declare sus fuentes y elija la ruta de evidencia adecuada.

```bash
python eval/run_eval.py     # -> eval/resultados.json + eval/resultados.md
```

| Caso | Qué prueba |
|------|-----------|
| 1 | Obra CON episodio → cita órdenes de cambio (evidencia directa) |
| 2 | Proyecto SIN episodio → declara inferencia estadística |
| 3 | Riesgo ALTO → drivers SHAP correctos con números exactos |
| 4 | Riesgo BAJO → factores protectores ("qué se hizo bien") |
| 5 | Mitigación de alcance → recupera el procedimiento correcto |

Métricas: precisión de invocación de tools, exactitud factual, cobertura de citación,
ruta de evidencia, precisión de recuperación. El harness es adversarial-ready (detecta
un número mal citado, una tool omitida o un disclaimer ausente). Con `AGENT_MODE=claude`
evalúa al LLM real con las mismas comprobaciones — ahí el 100% no está garantizado, y esa
comparación mock-vs-Claude es el valor real del harness.

## Métricas del modelo (validación cruzada, 200 obras)

| Target | R² (RepeatedKFold) | AUC (clasificación) |
|--------|--------------------|---------------------|
| desvío costo | +0.48 | 0.87 |
| desvío tiempo | +0.35 | 0.85 |

Validación de bandas: la banda ALTO concentra ~83% (costo) y ~81% (tiempo) de las
obras con desvío alto real; la banda BAJO ~14%. Ver `core/ml/artifacts/metrics.json`.
