---
tipo: semantica
titulo: Causas de desvío de costo en obra
tags: [causas, alcance, diseño, sitio, normativa, proveedor, clima, atribucion]
relacionados: [mitigacion-cambio-alcance, mitigacion-error-diseno, mitigacion-condicion-sitio, mitigacion-proveedores]
---

# Causas de desvío de costo en obra

El sobrecosto de una obra rara vez tiene una sola causa. En el análisis forense
de órdenes de cambio se clasifica cada evento en una de estas **seis categorías**
(alineadas con la práctica de *variance analysis* de AACE y con la propuesta técnica
del proyecto):

| Categoría | Qué es | Evidencia de origen |
|---|---|---|
| **Cambio de alcance** | El cliente añade o modifica requerimientos respecto al contrato original. | Orden de cambio — motivo declarado |
| **Error u omisión de diseño** | Planos incompletos o con interferencias que obligan a rehacer trabajo. | Orden de cambio — partida afectada |
| **Condición de sitio imprevista** | El terreno o el entorno difieren de lo esperado (nivel freático, roca, accesos). | Orden de cambio — descripción |
| **Ajuste normativo** | Exigencia de la autoridad surgida durante la ejecución. | Orden de cambio — descripción |
| **Proveedor / suministro** | Alza de precios o retrasos de materiales frente a la cotización inicial. | Orden de cambio — partida afectada |
| **Clima** | Paralizaciones o daños por condiciones climáticas adversas. | Orden de cambio — descripción |

## Peso relativo observado (estudio piloto)

Sobre el subconjunto del histórico con órdenes de cambio reconstruidas (~20% de las
obras), la atribución agregada del sobrecosto por causa es:

- **Error u omisión de diseño** — ~31 %
- **Cambio de alcance** — ~29 %
- **Proveedor / suministro** — ~19 %
- **Condición de sitio imprevista** — ~16 %
- **Ajuste normativo** — ~5 %
- **Clima** — ~1 %

> Estas proporciones provienen de un **estudio piloto** (calibración forense sobre
> un subconjunto), no de conclusiones generalizables al 100 % del histórico. Ver
> `atribucion_agregada.json`.

## Diferencia entre causa estructural y causa de ejecución

- La **causa estructural** (por qué una obra *estaba expuesta* a desviarse) la explica
  el modelo vía SHAP: variables de diseño como el avance, los niveles o la superficie.
  Ver [[variables-del-modelo]].
- La **causa de ejecución** (qué *efectivamente* ocurrió) la explican las órdenes de
  cambio de la memoria episódica. Ambas se complementan: la primera es *ex-ante*, la
  segunda *ex-post*.
