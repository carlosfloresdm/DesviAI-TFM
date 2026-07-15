---
tipo: semantica
titulo: Bandas de riesgo BAJO / MEDIO / ALTO
tags: [riesgo, bandas, clasificacion, score, probabilidad]
relacionados: [variables-del-modelo, causas-de-desvio]
---

# Bandas de riesgo BAJO / MEDIO / ALTO

El sistema no solo estima la magnitud del desvío (regresión); también clasifica cada
obra en una **banda de riesgo** a partir de la probabilidad de que tenga un desvío
"por encima de lo normal" (por encima de la mediana histórica). Es el indicador más
fiable para alerta temprana.

## Cortes

Sobre la probabilidad `p` del clasificador:

- **BAJO** — `p < 0.33`
- **MEDIO** — `0.33 ≤ p < 0.66`
- **ALTO** — `p ≥ 0.66`

## Qué significan en la práctica (validación sobre el histórico)

Porcentaje de obras de cada banda que **realmente** tuvieron desvío alto:

| Banda | Desvío de costo | Desvío de plazo |
|---|---|---|
| BAJO | ~14 % | ~14 % |
| MEDIO | ~47 % | ~60 % |
| ALTO | ~83 % | ~81 % |

El crecimiento fuerte de BAJO a ALTO confirma que las bandas separan bien el riesgo.
Una obra en banda **ALTO** tiene ~8 de cada 10 probabilidades de terminar con desvío
por encima de lo normal.

## Interpretación de la banda MEDIO

MEDIO significa que el modelo **no tiene señal clara**. No es "riesgo intermedio
garantizado", sino incertidumbre: conviene revisión manual y apoyarse en casos
similares y en la memoria episódica antes de decidir.

## Relación con el score de riesgo contextual

La banda del clasificador es solo **uno** de los tres componentes del score de riesgo
contextual, junto con el desempeño real de los proyectos vecinos y la señal de la
memoria episódica. Ver definición del score en la documentación del sistema.
