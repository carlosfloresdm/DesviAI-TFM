# Guía del proyecto DesviAI (para entenderlo fácil)

Este documento explica **qué es DesviAI, cómo funciona y qué hay en cada carpeta**, en
lenguaje sencillo. Es el mapa del proyecto; para arrancarlo, ver el [`README.md`](../README.md).

---

## 1. ¿Qué es DesviAI, en una frase?

Un sistema que, a partir de los datos de una obra al inicio, **predice cuánto se va a
desviar en costo y en plazo, la clasifica por riesgo, y explica el porqué** — con un
agente que responde preguntas citando siempre su fuente.

Tiene **dos partes**:

1. **El modelo predictivo (ya estaba hecho, no se toca):** un *Random Forest* entrenado con
   200 obras que estima el desvío y una clasificación que asigna banda de riesgo (BAJO /
   MEDIO / ALTO).
2. **La capa de diagnóstico (lo nuevo del PoC):** memorias, un "análisis de contexto de gestión"
   y un agente conversacional que explica *qué se hizo bien, qué se hizo mal y qué aprender*.

---

## 2. ¿Cómo funciona? (el flujo en 6 capas)

```
Datos de la obra
      │
  [1] Modelo Random Forest + clasificación  → desvío estimado + banda de riesgo
      │
  [2] SHAP            → qué variables explican el riesgo (causa estructural)
  [3] Órdenes de cambio (memoria episódica) → qué pasó de verdad (causa de ejecución)
  [4] Análisis de contexto de gestión       → riesgo de gestión (checklist opcional)
  [5] Memorias .md (conceptos, mitigaciones)→ base de conocimiento
      │
  [6] Agente conversacional → junta todo y responde en lenguaje natural, citando la fuente
      (internamente compara con obras parecidas vía kNN para dar evidencia estadística)
```

El diagrama visual está en **[`arquitectura.html`](../arquitectura.html)**
(o en vivo: https://desviai.onrender.com/arquitectura.html).

---

## 3. ¿Cómo verlo funcionando?

| Forma | Cómo | Para quién |
|-------|------|-----------|
| **Enlace en vivo** | https://desviai.onrender.com | El profesor / cualquiera (solo un clic) |
| **Docker** | `docker compose up --build` → http://localhost:8200 | Quien tenga Docker |
| **Nativo** | ver `README.md` (venv + `runserver`) | Para desarrollar |

---

## 4. Mapa de carpetas (qué hay y para qué sirve)

```
DESVIAI_TFM/
├── README.md              Cómo instalar y arrancar
├── PLAN.md                El plan del PoC y por qué se tomó cada decisión
├── CONTRIBUTING.md        Cómo trabajar en equipo (para principiantes en GitHub)
├── arquitectura.html      Diagrama de arquitectura (1 página)
│
├── DesviAI.html           La interfaz web (la página principal)
├── *.jsx / styles.css     Pantallas de la interfaz (ver detalle abajo)
│
├── Dockerfile             Receta para empaquetar todo en un contenedor
├── docker-compose.yml     Para levantarlo con un comando
│
├── docs/                  Guías
│   ├── GUIA_DEL_PROYECTO.md   ← este documento
│   ├── GUION_DEMO.md          Guion para presentar la demo
│   └── PROBAR_CON_DOCKER.md   Instrucciones para probar con Docker
│
├── knowledge/            LA MEMORIA del sistema (archivos .md, sin base de datos)
│   ├── semantica/            Conceptos: causas de desvío, tipologías, bandas, variables
│   ├── procedural/           Guías de mitigación por causa + checklist de arranque
│   └── episodica/            Un archivo por obra cerrada: qué se predijo vs. qué pasó
│
└── backend/             EL CEREBRO: servidor Django (API + modelo + agente)
    ├── manage.py            Arranca el servidor
    ├── requirements.txt     Librerías de Python que necesita
    ├── config/              Configuración de Django (settings, rutas)
    ├── eval/                Evaluación del agente (los 5 casos canónicos)
    └── core/
        ├── ml/              EL MODELO
        │   ├── train.py         Entrena el modelo y guarda los "artefactos"
        │   ├── features.py      Prepara las variables (igual en entrenamiento y uso)
        │   ├── predictor.py     Predice desvío + banda + intervalo de confianza
        │   ├── explainer.py     Explicabilidad SHAP
        │   ├── contexto.py      Análisis de contexto de gestión (checklist 8 tipos)
        │   ├── similares.py     Busca obras parecidas (kNN) — herramienta interna del agente
        │   ├── historico.py     Resume las 200 obras (para el dashboard)
        │   ├── gen_memoria.py   Genera las órdenes de cambio y los episodios .md
        │   └── artifacts/       Modelos entrenados (.pkl) — se generan, no se suben a git
        ├── agent/           EL AGENTE conversacional
        │   ├── tools.py         Las 4 herramientas que el agente puede usar
        │   ├── mock.py          Versión sin IA (respuestas fijas, para demo sin coste)
        │   ├── claude_loop.py   Versión con IA real (Claude) — se activa con una API key
        │   └── service.py       Elige entre mock y Claude
        ├── memory.py        Lee los archivos .md de knowledge/
        ├── views_api.py     Los endpoints de la API (predict, explain, agent/chat, …)
        └── views_front.py   Sirve la interfaz web
```

### Las pantallas de la interfaz (`*.jsx`)

La interfaz es React "sin compilar" (se traduce en el navegador), así que son archivos
sueltos, uno por pantalla:

| Archivo | Pantalla |
|---------|----------|
| `screen-login.jsx` | Inicio de sesión (demo: acepta cualquier cosa) |
| `screen-dashboard.jsx` | Resumen: cartera de 200 obras y distribución de riesgo |
| `screen-form.jsx` | Formulario para una nueva predicción |
| `screen-pipeline.jsx` | Animación "analizando…" |
| `screen-report.jsx` | El reporte con predicción, SHAP y análisis de contexto de gestión |
| `screen-chat.jsx` / `floating-chat.jsx` | El chat con el agente |
| `screen-extra.jsx` | Historial y configuración |
| `shared.jsx` | Piezas comunes + el cliente que llama a la API |
| `app.jsx` | Arma todo y coordina las pantallas |

---

## 5. Conceptos clave (glosario rápido)

- **Random Forest:** el modelo que predice el desvío. Es un conjunto de muchos "árboles de
  decisión" que votan; captura relaciones no lineales.
- **Banda de riesgo (BAJO/MEDIO/ALTO):** clasificación del riesgo de una obra. Es el
  indicador más fiable para alerta temprana.
- **SHAP:** técnica que descompone una predicción en cuánto aporta cada variable. Responde
  *"¿por qué el modelo predice esto?"*.
- **kNN (casos similares):** busca las obras históricas más parecidas para dar evidencia
  comparativa.
- **Órdenes de cambio:** eventos que encarecieron una obra (cambio de alcance, error de
  diseño, etc.). Son la evidencia "forense" de por qué se desvió.
- **Las 3 memorias** (idea central del proyecto):
  - **Semántica** = lo que el sistema *sabe* (conceptos).
  - **Procedural** = *cómo se hace* (procedimientos de mitigación).
  - **Episódica** = lo que *pasó* (un episodio por obra, con sus órdenes de cambio).
- **Análisis de contexto de gestión:** un checklist opcional de 8 tipos de riesgo sobre la
  gestión de la obra (madurez del ejecutivo, permisos, terreno, contrato, cliente…) que una
  fórmula determinística convierte en una banda BAJO/MEDIO/ALTO. El agente lo *explica*, no
  lo inventa.
- **Análisis de contexto de gestión:** una segunda lectura de riesgo, *opcional y paralela*
  al modelo: un checklist de preguntas concretas sobre la gestión de la obra (madurez del
  proyecto ejecutivo, permisos, terreno, contrato, cliente) que una fórmula determinística
  convierte en una banda BAJO/MEDIO/ALTO. El modelo mira las *dimensiones* de la obra; este
  análisis mira su *gestión* — se leen en conjunto, no compiten. El checklist se responde
  en la **entrada de datos** (junto a los parámetros del proyecto, si el usuario lo activa)
  y el resultado aparece en el reporte.
- **Agente conversacional:** responde preguntas usando "herramientas" (SHAP, memorias, kNN)
  y **cita la fuente de cada afirmación**. Su única decisión propia es elegir entre
  *evidencia directa* (si la obra tiene órdenes de cambio) o *evidencia estadística* (si no).

---

## 6. "Quiero ver X, ¿dónde miro?"

| Quiero entender… | Miro… |
|------------------|-------|
| El modelo y sus métricas | `backend/core/ml/train.py` y `backend/README.md` |
| Cómo se prepara una predicción | `backend/core/ml/predictor.py` + `features.py` |
| El análisis de contexto de gestión | `backend/core/ml/contexto.py` |
| El agente y sus herramientas | `backend/core/agent/` |
| Las memorias | carpeta `knowledge/` (son archivos de texto legibles) |
| Cómo se evalúa el agente | `backend/eval/run_eval.py` |
| Las decisiones de diseño | `PLAN.md` |
| Cómo presentar la demo | `docs/GUION_DEMO.md` |

---

## 7. Lo que es y lo que no es

- **Es** un *prototipo* (PoC) para demostrar la idea, deliberadamente simple y auditable.
- El **dataset** son 200 obras (50 reales + 150 sintéticas) y las **órdenes de cambio** son
  un *estudio piloto reconstruido* para ~20% de las obras — declarado como tal, no oculto.
- El **agente** funciona en modo "mock" (sin IA) por defecto para que la demo sea gratis y
  reproducible; con una API key de Anthropic se activa la versión con IA real.
