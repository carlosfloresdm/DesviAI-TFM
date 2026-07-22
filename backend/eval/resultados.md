# Evaluación del agente — 5 casos canónicos

## Métricas agregadas

| Métrica | Aciertos | % |
|---|---|---|
| Precisión de invocación de tools | 5/5 | 100% |
| Exactitud factual | 5/5 | 100% |
| Cobertura de citación | 5/5 | 100% |
| Ruta de evidencia | 3/3 | 100% |
| Precisión de recuperación | 1/1 | 100% |
| Clasificación de intención | 2/2 | 100% |
| **Global** | **21/21** | **100%** |

## Detalle por caso

### Caso 1 — Obra CON episodio — ¿por qué se desvió?
- **Pregunta:** ¿Por qué se desvió esta obra?  ·  obra_id: 44  ·  modo: mock
- **Tools:** consultar_shap → buscar_episodio
- **Checks:** 5/5
  - [x] invoca consultar_shap y buscar_episodio
  - [x] usa evidencia DIRECTA
  - [x] cita el desvío real (14.24%)
  - [x] cita la causa dominante (cambio de alcance)
  - [x] declara la fuente
- **Respuesta:**

  > Estructuralmente, el modelo predice un desvío de costo de 9.28% (media histórica 4.88%). Los factores que MÁS lo empujan al alza son: nivel de avance del proyecto (+3.15 pts), densidad (unidades por nivel) (+0.31 pts), número de unidades (+0.29 pts). Esta es la causa ex-ante (SHAP, capa 2).
  > 
  > En la EJECUCIÓN real, esta obra (id 44) tuvo un desvío de costo de 14.24%, y la evidencia forense DIRECTA (órdenes de cambio) lo atribuye a: cambio de alcance, condición de sitio imprevista, ajuste normativo, proveedor / suministro, con cambio de alcance como causa dominante. Fuente: memoria episódica (órdenes de cambio del proyecto).

### Caso 2 — Proyecto SIN episodio — ¿qué explica el riesgo?
- **Pregunta:** ¿Qué explica el riesgo de este proyecto?  ·  obra_id: None  ·  modo: mock
- **Tools:** consultar_shap → buscar_episodio → buscar_casos_similares
- **Checks:** 4/4
  - [x] invoca SHAP + episodio + similares
  - [x] declara inferencia ESTADÍSTICA
  - [x] aclara que NO es evidencia directa
  - [x] declara la fuente
- **Respuesta:**

  > Estructuralmente, el modelo predice un desvío de costo de 6.47% (media histórica 4.88%). Los factores que MÁS lo empujan al alza son: nivel de avance del proyecto (+2.12 pts), experiencia alta del equipo (+0.14 pts). Esta es la causa ex-ante (SHAP, capa 2).
  > 
  > NO hay órdenes de cambio documentadas para este proyecto, así que la atribución de causa es una inferencia ESTADÍSTICA, no evidencia directa: de 5 obras comparables, 4 tuvieron desvío de costo alto real (tasa 80%). Entre las comparables con episodio documentado (18), las causas típicas son diseño y alcance. Fuente: casos similares (capa 4) + patrones agregados (capa 3).

### Caso 3 — Riesgo ALTO — drivers estructurales (SHAP)
- **Pregunta:** ¿Qué explica el riesgo alto de este proyecto?  ·  obra_id: None  ·  modo: mock
- **Tools:** consultar_shap → buscar_episodio → buscar_casos_similares
- **Checks:** 4/4
  - [x] invoca consultar_shap
  - [x] cita el driver SHAP top ('nivel de avance del proyecto')
  - [x] cita la predicción (8.7%)
  - [x] declara la capa/fuente
- **Respuesta:**

  > Estructuralmente, el modelo predice un desvío de costo de 8.7% (media histórica 4.88%). Los factores que MÁS lo empujan al alza son: nivel de avance del proyecto (+1.98 pts), velocidad de obra (m²/día) (+0.40 pts), m² por unidad (+0.30 pts). Esta es la causa ex-ante (SHAP, capa 2).
  > 
  > NO hay órdenes de cambio documentadas para este proyecto, así que la atribución de causa es una inferencia ESTADÍSTICA, no evidencia directa: de 5 obras comparables, 4 tuvieron desvío de costo alto real (tasa 80%). Entre las comparables con episodio documentado (143, 72), las causas típicas son diseño y alcance. Fuente: casos similares (capa 4) + patrones agregados (capa 3).

### Caso 4 — Riesgo BAJO — ¿qué se hizo bien?
- **Pregunta:** ¿Qué se hizo bien en esta obra?  ·  obra_id: 127  ·  modo: mock
- **Tools:** consultar_shap → buscar_episodio
- **Checks:** 4/4
  - [x] clasifica intención 'qué se hizo bien'
  - [x] invoca consultar_shap
  - [x] cita un factor protector (SHAP negativo)
  - [x] declara la fuente
- **Respuesta:**

  > A favor del proyecto (factores que REDUCEN el desvío según SHAP): nivel de avance del proyecto (-2.72 pts), experiencia alta del equipo (-0.44 pts), velocidad de obra (m²/día) (-0.38 pts). Estos son los aspectos estructurales que lo acercan al perfil de bajo desvío. En la ejecución real, la obra 127 cerró con un desvío de costo de 0.28% (riesgo BAJO): confirma que las decisiones estructurales fueron acertadas. Fuente: explicabilidad estructural (capa 2).

### Caso 5 — Mitigación de cambio de alcance (recuperación)
- **Pregunta:** ¿Cómo mitigo el riesgo de cambio de alcance?  ·  obra_id: None  ·  modo: mock
- **Tools:** consultar_shap → leer_memoria
- **Checks:** 4/4
  - [x] clasifica intención 'mitigación'
  - [x] invoca leer_memoria
  - [x] recupera el procedimiento de ALCANCE
  - [x] declara la fuente
- **Respuesta:**

  > Para mitigar el riesgo, el foco debe estar en la causa que mencionas (cambio de alcance). Procedimiento recomendado:
  >   1. Congelar el alcance base antes de iniciar obra: acta firmada de requerimientos, planos y especificaciones, con número de versión.
  >   2. Procedimiento formal de control de cambios: todo requerimiento nuevo entra por una orden de cambio con impacto de costo y plazo cuantificado *antes* de ejecutarse.
  >   3. Umbral de aprobación escalonado: cambios menores los aprueba el jefe de obra; por encima de un % del contrato, requieren aprobación de dirección y del cliente.
  >   4. Registro acumulado visible: llevar el total de cambios aprobados como % del contrato; si supera ~5 %, activar revisión de contingencia.
  > Fuente: memoria procedural [[mitigacion-cambio-alcance]].
