# Decisiones sobre variables excluidas del modelo

Este documento justifica, con evidencia empírica, dos decisiones de diseño del
modelo predictivo de desvíos de obra: la exclusión de las **variables temporales**
(en particular el año de inicio) y la exclusión de las **variables
macroeconómicas**. Ambas decisiones se tomaron midiendo el efecto sobre el
rendimiento del modelo en validación cruzada, no por intuición.

**Metodología común a ambas pruebas.** Todas las comparaciones usan validación
cruzada de 5 particiones (5-fold cross-validation), que mide el rendimiento del
modelo sobre obras que *no* se usaron para entrenarlo. Es la forma correcta de
detectar si una variable ayuda a *predecir* (generalizar a casos nuevos) o sólo
ayuda a *memorizar* los datos de entrenamiento. Las métricas son R² para la
regresión del desvío y AUC para la clasificación del riesgo. El modelo es el
mismo Random Forest de producción, con sus hiperparámetros ya ajustados.

---

## 1. Exclusión de las variables temporales (año, mes, trimestre)

### El problema

El modelo original incluía tres variables derivadas de la fecha de inicio:
`año_inicio`, `mes_inicio` y `trimestre_inicio`. La variable de año generaba un
problema estructural: como el año siempre avanza, **toda obra futura cae fuera
del rango de entrenamiento** (2016–2024). Al predecir una obra de 2026 o 2027, el
modelo recibía un valor de año que nunca había visto, y debía extrapolar. Esto
es relevante en la práctica, porque toda obra real cargada de ahora en adelante
tendrá una fecha posterior al rango de entrenamiento.

### La medición

Se compararon tres configuraciones: el modelo con las tres temporales, el modelo
quitando sólo el año, y el modelo quitando las tres.

| Métrica | Con las 3 temporales | Sin el año | Sin las 3 |
|---|---|---|---|
| R² costo | 0.500 | 0.508 | **0.510** |
| R² plazo | 0.377 | 0.380 | **0.384** |
| AUC costo | 0.866 | — | **0.880** |
| AUC plazo | 0.836 | — | **0.842** |

Adicionalmente, se midió el peso de cada temporal en el modelo (importancia de
variables del Random Forest): el año pesaba 4,7 % en costo y 1,5 % en plazo; el
mes y el trimestre, menos del 2,5 % combinados.

### La conclusión

Quitar las variables temporales **no empeora el modelo: lo mejora levemente en
las cuatro métricas**. La interpretación es que el año no aportaba señal
generalizable, sino señal atada a años concretos del pasado: el modelo había
asociado ciertos años con ciertos niveles de desvío (probablemente capturando, de
forma indirecta, el contexto económico de cada año), pero esa asociación no se
proyecta de manera fiable hacia el futuro. En otras palabras, el peso del 4,7 %
del año no era información útil, sino una fuente de error que se activaba
justamente al predecir obras nuevas.

Quitar las tres temporales tuvo un doble beneficio: mejoró marginalmente el
rendimiento y **eliminó de raíz el problema de extrapolación temporal**. Tras el
cambio, una misma obra cargada con fecha de 2024, 2026 o 2027 produce un
resultado idéntico, porque la fecha ya no influye en la predicción.

**Decisión adoptada:** se excluyeron `año_inicio`, `mes_inicio` y
`trimestre_inicio` del modelo (de 17 a 14 variables). La fecha de inicio se sigue
solicitando al usuario y figura como dato descriptivo de la obra en el informe,
pero no se convierte en variable predictiva.

---

## 2. Exclusión de las variables macroeconómicas

### El contexto

Se evaluó un conjunto de datos macroeconómicos mensuales (120 meses, enero 2016 a
diciembre 2025) con seis indicadores: inflación mensual, tipo de cambio y su
variación, PIB trimestral, variación de un índice de precios (IPMC) y salario
mínimo. El rango cubría la totalidad de las fechas de las 200 obras, de modo que
toda obra tenía datos macroeconómicos asociados.

La hipótesis a evaluar era si el contexto macroeconómico de cada obra mejora la
predicción del desvío. La prueba se diseñó con especial cuidado para descartar
que un resultado negativo se debiera a una codificación inadecuada de las
variables (un riesgo conocido al trabajar con datos macroeconómicos).

### Las mediciones

**Prueba A — Dos formas de asociar la macro a cada obra.** Se probaron dos
codificaciones: los indicadores del mes de inicio de la obra, y el promedio de
los indicadores a lo largo de los meses de ejecución (esta segunda es
conceptualmente superior, porque una obra dura aproximadamente dos años y el
contexto que la afecta es el de toda su ejecución, no sólo el de su mes inicial).

| Métrica | Base (sin macro) | + macro (mes inicio) | + macro (ejecución) |
|---|---|---|---|
| R² costo | **0.510** | 0.491 | 0.461 |
| R² plazo | **0.384** | 0.363 | 0.381 |
| AUC costo | **0.880** | 0.841 | 0.857 |
| AUC plazo | **0.842** | 0.833 | 0.837 |

**Prueba B — Cada variable por separado.** Para descartar que el problema fuera
el exceso de variables agregadas de golpe, se probó añadir cada indicador
macroeconómico individualmente (en su forma de ejecución), sobre el R² de costo
(base = 0,510):

| Variable agregada | R² costo | Efecto |
|---|---|---|
| inflación mensual | 0.485 | empeora |
| tipo de cambio | 0.501 | empeora |
| variación tipo de cambio | 0.503 | empeora |
| PIB trimestral | 0.497 | empeora |
| variación IPMC | 0.504 | empeora |
| salario mínimo | 0.498 | empeora |

### La conclusión

En todas las configuraciones probadas, agregar variables macroeconómicas
**empeora el rendimiento del modelo**. El resultado es robusto: se mantiene tanto
con la codificación por mes de inicio como con la de ejecución, y tanto al
agregar las seis variables juntas como al agregarlas de a una. Ninguna variable
macroeconómica, en ninguna forma, mejora la predicción.

La causa más probable es la **naturaleza del objetivo de predicción**. El modelo
predice el desvío *porcentual* respecto del presupuesto inicial, no el costo
final absoluto. El presupuesto inicial de cada obra ya fue elaborado por
profesionales que conocían la inflación esperada, de modo que el efecto
macroeconómico ya está incorporado en la línea de base contra la que se mide el
desvío. Al calcular el desvío como porcentaje, el componente macroeconómico se
cancela en buena medida (afecta numerador y denominador en la misma dirección), y
lo que queda como desvío depende sobre todo de factores de gestión: el nivel de
definición del proyecto y la experiencia del equipo. Esto es coherente con la
importancia de variables del modelo, donde el nivel de avance del proyecto
explica por sí solo más del 60 % de la predicción.

Que las variables macroeconómicas *empeoren* el modelo (en lugar de simplemente
no aportar) se explica porque, al no contener señal aprovechable para este
objetivo, sólo agregan dimensiones donde el modelo encuentra patrones espurios
que perjudican la generalización a obras nuevas.

**Decisión adoptada:** se excluyeron las variables macroeconómicas del modelo,
confirmando con evidencia la decisión que ya se había tomado de forma
preliminar.

### Alcance de esta conclusión

Esta prueba demuestra que las variables macroeconómicas no mejoran la predicción
**del desvío porcentual, con este conjunto de datos**. No debe generalizarse a la
afirmación de que el contexto macroeconómico sea irrelevante para la construcción
en general. Si el objetivo de predicción cambiara —por ejemplo, predecir el costo
final absoluto en lugar del desvío porcentual— el efecto inflacionario dejaría de
cancelarse y las variables macroeconómicas pasarían, con alta probabilidad, a ser
relevantes. La exclusión es la decisión correcta para el diseño actual del
modelo, no una conclusión universal.

---

## Resumen

| Variables | Decisión | Evidencia |
|---|---|---|
| Temporales (año, mes, trimestre) | Excluidas | Mejoran las 4 métricas al quitarlas; además eliminan la extrapolación a fechas futuras |
| Macroeconómicas (6 indicadores) | Excluidas | Empeoran el modelo en toda configuración probada (por mes/ejecución, juntas/individuales) |

Ambas decisiones comparten una lección metodológica: en un modelo predictivo,
**más variables no implican un mejor modelo**. Las variables sin señal
generalizable para el objetivo concreto introducen ruido que perjudica la
capacidad de predecir casos nuevos. La validación cruzada es la herramienta que
permite distinguir las variables que ayudan a predecir de las que sólo ayudan a
memorizar.
