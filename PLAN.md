# DesviAI — Plan de implementación PoC/MVP (TFM)

> Sistema de predicción y diagnóstico de desvío de costos/plazos en obras de construcción.
> Modelo cerrado (Random Forest + SHAP) · Agente conversacional con memoria contextual · UI DesviAI.

**Fecha del plan:** 2026-07-13
**Hitos:** PoC → ~1 semana (presentación al profesor) · MVP → 2-4 semanas después.

---

## 1. Decisiones tomadas

| Tema | Decisión |
|------|----------|
| Modelo predictivo | **Cerrado, no se toca.** Random Forest por target (`desvio_costo` R²=0.48, `desvio_tiempo` R²=0.35) + clasificación logística de riesgo (AUC 0.87/0.85). Se exporta del notebook a artefactos joblib. |
| Backend | **Django** (sirve la UI estática de DesviAI + API JSON en el mismo proceso). |
| Frontend | UI DesviAI existente (React + Babel standalone). PoC: solo **reporte + chat** conectados. MVP: todas las pantallas. |
| Base de conocimiento | **Sin RAG/vectores** (feedback del profesor). Archivos `.md` relacionados estilo OKF/Obsidian, organizados en 3 memorias: semántica, procedural, episódica. |
| Órdenes de cambio | **Sintéticas coherentes** para ~25% de las obras: la suma de impactos cuadra con la brecha real `presupuesto_final − presupuesto_inicial`. Declaradas como estudio piloto reconstruido. |
| Agente | Tool calling con decisión binaria acotada (evidencia directa vs. inferencia agregada). **Modo `mock` determinístico** hasta tener API key de Anthropic; el mismo código pasa a Claude con una variable de entorno. |
| Score de riesgo contextual | Fórmula determinística (ver §3). El LLM lo narra, no lo calcula. |
| Evaluación | 5 casos canónicos con métricas (exigencia del profesor). |

---

## 2. Arquitectura (versión sencilla — 1 página)

```
                        ┌─────────────────────────────────────────┐
                        │           UI DesviAI (React)            │
                        │  formulario · reporte · chat · cierre   │
                        └───────────────┬─────────────────────────┘
                                        │ JSON
                        ┌───────────────▼─────────────────────────┐
                        │            Django (API)                 │
                        │  /api/predict  /api/explain             │
                        │  /api/similares  /api/score-contextual  │
                        │  /api/agent/chat  /api/historico        │
                        └───┬─────────┬─────────┬────────┬────────┘
                            │         │         │        │
            ┌───────────────▼──┐ ┌────▼────┐ ┌──▼─────┐ ┌▼──────────────────┐
            │ CAPA 1 (cerrada) │ │ CAPA 2  │ │ CAPA 4 │ │ MEMORIA (.md)     │
            │ RF costo/tiempo  │ │ SHAP    │ │ kNN    │ │ semántica         │
            │ + clf riesgo     │ │ local/  │ │ 3-5    │ │ procedural        │
            │ (joblib)         │ │ global  │ │ vecinos│ │ episódica (=capa3)│
            └──────────────────┘ └─────────┘ └────────┘ └───────────────────┘
                            \         |         |        /
                             \        |         |       /
                        ┌─────▼───────▼─────────▼──────▼─────┐
                        │   CAPA 6 — Agente (tool calling)   │
                        │  4 tools · 1 decisión binaria      │
                        │  auditable · log de invocaciones   │
                        │  modo: mock ⇄ Claude               │
                        └────────────────────────────────────┘
```

La capa 3 (forense) y la memoria episódica **son la misma cosa**: cada obra del subconjunto
piloto tiene un episodio `.md` con sus órdenes de cambio, la comparación predicho vs. real
y la lección aprendida.

---

## 3. Score de riesgo contextual (el mecanismo que pidió el profesor)

```
score_contextual = 100 × ( w₁ · prob_clasificador          ← modelo (capa 1)
                         + w₂ · tasa_desvio_alto_vecinos   ← kNN (capa 4)
                         + w₃ · señal_episodica )          ← memoria episódica
```

- **`prob_clasificador`**: probabilidad de desvío alto de la regresión logística (0-1).
- **`tasa_desvio_alto_vecinos`**: fracción de los k=5 vecinos más cercanos que tuvieron
  desvío alto real (0-1).
- **`señal_episodica`**: fracción de episodios de obras vecinas cuyas causas raíz aplican
  al proyecto consultado (misma tipología, experiencia baja, avance similar…) (0-1).
- Pesos iniciales: `w₁=0.5, w₂=0.3, w₃=0.2` (a calibrar contra el histórico en el MVP).

**Propiedades:** determinístico, cada componente citable, el LLM solo lo explica.
Ejemplo de narración: *"Score 72/100: el modelo da 0.81 de probabilidad de desvío alto,
3 de tus 5 obras comparables tuvieron desvío alto, y 2 episodios comparten tu factor de
riesgo dominante (cambio de alcance en postensado con equipo de baja experiencia)."*

---

## 4. Base de conocimiento — 3 memorias en `.md`

```
knowledge/
├── semantica/                        # QUÉ SABE — conceptos del dominio
│   ├── causas-de-desvio.md           # las 6 categorías + definiciones
│   ├── tipologias-constructivas.md   # postensado vs tradicional, riesgos típicos
│   ├── bandas-de-riesgo.md           # significado de BAJO/MEDIO/ALTO + tasas reales
│   └── variables-del-modelo.md       # qué significa cada feature y su efecto SHAP global
├── procedural/                       # CÓMO SE HACE — procedimientos correctos
│   ├── mitigacion-cambio-alcance.md
│   ├── mitigacion-error-diseno.md
│   ├── mitigacion-condicion-sitio.md
│   ├── mitigacion-proveedores.md
│   └── checklist-arranque-obra.md
└── episodica/                        # QUÉ PASÓ — un episodio por obra cerrada
    ├── obra-017.md                   # predicho vs real · órdenes de cambio · lección
    ├── obra-036.md
    └── ... (15 en PoC → ~50 en MVP)
```

Convenciones:
- **Front-matter YAML** en cada archivo: `tipo`, `tags`, `tipologia`, `categorias_causa`, `obra_id`.
- **Wikilinks** `[[nombre]]` entre memorias (episodio → procedimiento de mitigación → concepto).
- El agente recupera por tags/relaciones, no por embeddings. El corpus completo es pequeño
  (~60-80 archivos cortos) y cabe en contexto si hace falta.

---

## 5. Herramientas del agente (capa 6)

| Tool | Fuente | Devuelve |
|------|--------|----------|
| `consultar_shap(obra_id)` | Capa 2 | Ranking de variables con contribución en pts % |
| `buscar_episodio(obra_id)` | Memoria episódica | Episodio completo si existe (`existe_evidencia: true/false`) |
| `buscar_casos_similares(obra_id, k)` | Capa 4 | k vecinos + desempeño real + sus episodios si existen |
| `leer_memoria(tipo, tags)` | Semántica/procedural | Archivos `.md` filtrados por tipo y tags |

**Única decisión autónoma** (idéntica a la propuesta aprobada): si `buscar_episodio`
devuelve evidencia → citar órdenes de cambio como fuente directa; si no → usar vecinos +
inferencia agregada **declarando explícitamente que es estadística**.

Todo turno del agente registra en un log: tools invocadas, orden, argumentos y qué archivos
leyó → anexo de trazabilidad para la memoria del TFM.

Modo `mock` (sin API key): el loop ejecuta las mismas tools con heurísticas por tipo de
pregunta y arma la respuesta con plantillas alimentadas por datos reales. Cambiar
`AGENT_MODE=claude` activa el LLM sin tocar nada más.

---

## 6. Evaluación — 5 casos canónicos

| # | Caso | Qué prueba | Métricas |
|---|------|-----------|----------|
| 1 | Obra CON episodio, pregunta "¿por qué se desvió?" | Cita órdenes de cambio como evidencia directa | tool correcta · citación · exactitud factual |
| 2 | Obra SIN episodio, misma pregunta | Declara inferencia estadística, usa vecinos | disclaimer presente · tool correcta |
| 3 | Obra riesgo ALTO, "¿qué explica el riesgo?" | Drivers SHAP correctos con números exactos | números citados == valores SHAP |
| 4 | Obra riesgo BAJO, "¿qué se hizo bien?" | Factores protectores correctos | exactitud factual |
| 5 | "¿Cómo mitigo el riesgo de cambio de alcance?" | Recupera memoria procedural correcta | precisión de recuperación |

**Métricas agregadas:** exactitud factual (todo número citado coincide con su fuente),
cobertura de citación (% de afirmaciones con fuente), precisión de invocación de tools,
consistencia del score entre ejecuciones. Script `eval/run_eval.py` reproducible.

---

## 7. Fases y cronograma

### HITO 1 — PoC (~1 semana)

| Día | Entregable |
|-----|-----------|
| 1-2 | `train.py` reproduce el notebook → artefactos joblib. Django con `/api/predict`, `/api/explain`, `/api/similares`. IC80% real vía percentiles de los árboles del RF. |
| 2-3 | Órdenes de cambio sintéticas coherentes para 15 obras → episodios `.md`. Memorias semántica y procedural iniciales (~10 archivos). `/api/score-contextual`. |
| 3-4 | Agente: 4 tools + loop tool calling + modo mock + log de trazabilidad. `/api/agent/chat`. |
| 4-5 | 5 casos canónicos + script de evaluación + resultados. |
| 5-6 | Pantallas **reporte + chat** de DesviAI conectadas a la API (reporte rediseñado: bloques SOBRECOSTE y SOBREPLAZO con banda, probabilidad, desvío, IC, SHAP, similares y score contextual). |
| 6-7 | Diagrama de arquitectura 1 página + guion de demo + buffer. |

### HITO 2 — MVP (2-4 semanas después)

- DesviAI completo conectado: dashboard con datos reales del histórico, formulario con los
  10 campos del modelo, pipeline reflejando llamadas reales, historial, cierre de proyecto
  (el cierre genera un episodio nuevo en memoria episódica → "el sistema aprende del pasado").
- Memoria episódica ampliada a ~50 obras + tabla de atribución agregada por categoría.
- Agente en modo Claude (cuando haya API key) + comparativa mock vs. real en la evaluación.
- Calibración de pesos del score contextual contra el histórico.
- Validación cuantitativa (desvío predicho vs. real vs. % explicado) + guion para validación
  con expertos + documentación final.

---

## 8. Contrato de datos (entrada del modelo — fuente de verdad del formulario)

```python
{
  'sup_m2': 45000,                          # int
  'niveles': 35,                            # int
  'unidades': 400,                          # int
  'presupuesto_inicial': 30_000_000,        # int (USD)
  'tiempo_inicial': 730,                    # int (días)
  'sistema_constructivo': 'Concreto Postensado',  # | 'Concreto Tradicional'
  'nivel_acabado': 'Medio',                 # Básico | Medio | Alto
  'avance_proyecto': '70 - 80',             # '60 - 70' | '70 - 80' | '80 - 90' | '90 - 100'
  'proyectos_similares': '10 - 15',         # rangos; ≥15 ⇒ experiencia_alta=1
  'fecha_inicio': '2024-03',                # YYYY-MM
}
```

---

## 9. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| API key no llega antes del PoC | Modo mock completo; la demo no depende del LLM. |
| Órdenes sintéticas cuestionadas | Framing ya aprobado en la propuesta: "estudio piloto reconstruido", suma cuadra con brecha real, sesgo de selección declarado. |
| Alcance del PoC se infla | El profesor pidió SIMPLE: solo 2 pantallas, 15 episodios, mock. Todo lo demás es MVP. |
| UI-modelo desalineados | Contrato de datos de §8 congela el formulario; el reporte muestra solo lo que el modelo realmente produce. |

## 10. Pendientes externos

- [ ] API key de Anthropic (activa modo real del agente).
- [ ] Confirmar si Django es requisito formal del máster o preferencia (afecta cuánto ORM/templates "canónicos" usar y cómo justificarlo en la memoria).
- [ ] Fechas exactas de la reunión del PoC y de la presentación del MVP.
