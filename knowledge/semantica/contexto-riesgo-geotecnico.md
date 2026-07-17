---
tipo: semantica
titulo: Contexto de gestión — Riesgo geotécnico y entorno físico
tags: [contexto, gestion, geotecnico, suelos, terreno, cimentacion]
relacionados: [mitigacion-condicion-sitio, causas-de-desvio]
---

# Riesgo geotécnico y entorno físico

**Tipo de riesgo contextual:** 3 · Riesgo base (incide sobre todo en el costo)

## Concepto

Mide la incertidumbre sobre el terreno y su entorno. La ausencia de estudio de
suelos específico se trata como el peor escenario posible para esa zona: lo que no
se conoce, aparece como sorpresa (y sobrecosto) durante la cimentación.

## Señales que lo componen

- Existencia de mecánica de suelos específica del terreno
- Densidad de sondeos vs. superficie
- Variabilidad entre sondeos (homogéneo vs. heterogéneo)
- Historial geológico de la zona (relleno, cauce, terreno natural)
- Profundidad y estacionalidad de la napa freática
- Infraestructura subterránea no documentada
- Época del año del movimiento de tierras

## Nota de implementación

Algunas señales (historial geológico) idealmente vendrían de bases geográficas
externas. En el PoC se cargan **manualmente**; la integración automática es futura.

## Lectura de riesgo

- **Bajo:** estudio de suelos completo, terreno homogéneo y conocido.
- **Medio:** estudio con pocos sondeos, o alguna incertidumbre de entorno.
- **Alto:** sin estudio de suelos, zona de relleno o napa alta.

## Relacionado

Este tipo anticipa la causa de ejecución «condición de sitio imprevista» de
[[causas-de-desvio]]. Procedimiento: [[mitigacion-condicion-sitio]].
