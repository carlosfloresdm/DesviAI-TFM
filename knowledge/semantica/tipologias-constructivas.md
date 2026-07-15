---
tipo: semantica
titulo: Tipologías constructivas
tags: [tipologia, postensado, tradicional, sistema-constructivo]
relacionados: [variables-del-modelo, mitigacion-proveedores]
---

# Tipologías constructivas

El histórico contiene dos sistemas constructivos, ambos para vivienda vertical:

## Concreto Postensado

Losas y elementos con cables tensados que permiten grandes luces y menos columnas.
Predomina en el histórico (~65 % de las obras).

- **Sensible a:** suministro y precio del acero de postensado, y a la secuencia de
  tensado (un retraso arrastra al resto del cronograma).
- **Riesgo típico:** partidas de estructura y fachada; dependencia de proveedor
  especializado. Ver [[mitigacion-proveedores]].

## Concreto Tradicional

Estructura convencional de columnas, vigas y losas armadas (~35 % del histórico).

- **Sensible a:** cambios de alcance y ajustes de diseño en obra, por su mayor
  flexibilidad de modificación.
- **Riesgo típico:** partidas de cimentación e instalaciones cuando el diseño llega
  incompleto.

## Nota del modelo

Aunque intuitivamente el sistema constructivo parece decisivo, en los datos aporta
**muy poca** señal predictiva por sí solo (SHAP global casi nulo). El riesgo se explica
mucho más por la configuración del proyecto —avance, densidad, experiencia del equipo—
que por la técnica estructural. Ver [[variables-del-modelo]].
