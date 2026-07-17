---
tipo: semantica
titulo: Contexto de gestión — Madurez del proyecto ejecutivo
tags: [contexto, gestion, madurez, ejecutivo, rfi, plazo]
relacionados: [mitigacion-madurez-ejecutivo, contexto-senales-ejecucion, variables-del-modelo]
---

# Madurez del proyecto ejecutivo

**Tipo de riesgo contextual:** 1 · Riesgo base (incide sobre todo en el plazo)

## Concepto

Mide qué tan completo y coordinado está el proyecto ejecutivo en el momento de
licitar e iniciar la obra: planos, especificaciones técnicas, catálogo de conceptos
y submittals. Un proyecto poco maduro se termina de definir *durante* la ejecución,
y esa definición tardía se traduce en RFIs, órdenes de cambio y retrabajo.

## Por qué importa

Históricamente, un proyecto ejecutivo al 60% de completitud genera cerca del **doble
de RFIs** que uno al 95%. Cada RFI sin responder a tiempo detiene o retrasa la
partida asociada. Es una de las causas más frecuentes de desvío de plazo, y arrastra
sobrecosto por la ineficiencia del retrabajo.

## Señales que lo componen

- % de planos emitidos para construcción vs. preliminares al licitar
- Antigüedad del proyecto ejecutivo (meses desde su cierre)
- Disciplinas sin coordinación BIM
- % de especificaciones completas vs. genéricas
- % de catálogo de conceptos cerrado al inicio
- Submittals requeridos vs. aprobados al inicio

## Lectura de riesgo

- **Bajo:** proyecto ≥90% emitido para construcción, especificaciones completas,
  coordinación BIM al día.
- **Medio:** entre 70% y 90%, con algunas disciplinas sin coordinar.
- **Alto:** por debajo del 70%, especificaciones genéricas, catálogo abierto.

## Relación con el modelo

En el checklist, la respuesta se pre-selecciona desde el campo `avance_proyecto`
del contrato del modelo (más avance ⇒ menos definición pendiente); el usuario
siempre puede corregirla. Ver [[mitigacion-madurez-ejecutivo]].
