---
tipo: semantica
titulo: Variables del modelo y su efecto
tags: [variables, features, shap, avance, explicabilidad]
relacionados: [bandas-de-riesgo, causas-de-desvio]
---

# Variables del modelo y su efecto

El modelo (Random Forest, uno por target) usa **14 variables conocidas al inicio de
la obra**. No usa información futura, ni variables temporales (año, mes o trimestre
de inicio), ni variables macroeconómicas: ambas familias fueron evaluadas y
excluidas con evidencia empírica de validación cruzada (ver
`docs/decisiones_variables.md`). La importancia de cada variable se mide con
**SHAP** (TreeSHAP): cuánto mueve, en promedio, la predicción del desvío.

## Ranking global (impacto medio |SHAP|)

**Desvío de costo** (promedio histórico ≈ 4.9 %):

1. **avance_ord** — nivel de avance del proyecto · *dominante, ~2.2 pts*
2. unidades_por_nivel — densidad del proyecto
3. velocidad_obra_m2_dia — m² construidos por día
4. presupuesto_diario — intensidad de gasto
5. m2_por_unidad — tamaño medio de la unidad

**Desvío de plazo** (promedio histórico ≈ 12.1 %):

1. **avance_ord** — *aún más dominante, ~4.3 pts*
2. presupuesto_diario
3. presupuesto_inicial
4. unidades_por_nivel
5. niveles

## Lecturas clave

- El **nivel de avance del proyecto** (`avance_ord`) es, con diferencia, la variable
  más influyente en ambos desvíos. Concentra la mayor parte de la señal del modelo.
- La **experiencia del equipo** (≥15 proyectos similares) actúa como factor protector:
  reduce el desvío al cruzar ese umbral.
- El **sistema constructivo** (postensado vs. tradicional) aporta muy poco por sí solo:
  el riesgo se explica más por la configuración del proyecto que por la técnica.
- **La fecha de inicio no influye en la predicción.** Se solicita al usuario y figura
  como dato descriptivo en el informe, pero no entra al modelo: una misma obra
  cargada con fecha de 2024, 2026 o 2027 produce un resultado idéntico.

## Cómo usar esto en un diagnóstico

Para explicar por qué una obra concreta tiene su riesgo, no basta el ranking global:
se usa **SHAP local** (`/api/explain`), que descompone *esa* predicción variable por
variable. El ranking global da el contexto; el local da la causa estructural del caso.
Ver [[causas-de-desvio]] para la diferencia entre causa estructural y de ejecución.
