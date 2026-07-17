---
tipo: semantica
titulo: Contexto de gestión — Señales tempranas en ejecución (diferido)
tags: [contexto, gestion, ejecucion, rfi, ordenes-de-cambio, diferido]
relacionados: [contexto-madurez-ejecutivo, causas-de-desvio]
---

# Señales tempranas en ejecución

**Tipo de riesgo contextual:** 7 · Dinámico — **DIFERIDO en esta etapa**

## Concepto

Es el único tipo dinámico: no se evalúa una vez al inicio, sino que se
**actualiza durante la obra** cada vez que se registra un RFI, una orden de cambio
o un submittal rechazado. Funciona como un termómetro en tiempo real del riesgo
materializándose.

## Por qué está diferido

La plataforma actual predice **una sola vez** desde datos de diseño y no dispone
de un registro de ejecución donde alojar esta evolución temporal. Este tipo queda
**arquitectónicamente contemplado pero no implementado** en el PoC, listo para
activarse cuando exista una bitácora de obra que lo alimente. (El cierre de
proyecto del MVP, que genera episodios nuevos, es el candidato natural.)

## Señales que lo compondrían (a futuro)

- Volumen de RFIs (total y por fase)
- Tiempo promedio de respuesta a RFIs
- Tasa de conversión RFI → orden de cambio
- Órdenes de cambio por tipo (diseño / alcance / condición no prevista)
- Monto acumulado de órdenes de cambio como % del contrato
- Submittals rechazados o en revisión prolongada

## Relacionado

Los RFIs suelen originarse en la definición pendiente del ejecutivo:
ver [[contexto-madurez-ejecutivo]].
