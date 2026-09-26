# Grafos de memorias — presentación final

Visualizan cómo se conectan las tres memorias de DesviAI (episódica, semántica y
procedural). **Todo se genera desde la base de conocimiento real** (`knowledge/*.md` +
órdenes de cambio); nada está dibujado a mano.

| Archivo | Para qué |
|---------|----------|
| `grafo-memorias.html` | Vistas 1-3 para mostrar en vivo (un solo archivo, funciona sin servidor) |
| `red-interactiva.html` | Vista 4: red tipo Obsidian que se puede tocar (arrastrar, seleccionar, buscar) |
| `png/` | 14 imágenes 4K para diapositivas: 7 capturas × tema oscuro y claro |
| `build_data.py` | Regenera los datos desde las memorias y los inyecta en el HTML |
| `exportar_png.ps1` | Regenera los PNG con Microsoft Edge |

## Las vistas

1. **Una obra, tres memorias** — obras 118, 177 y 167: qué pasó → por qué pasó → qué hacer.
2. **La memoria como red** — las 40 obras: 40 episodios → 6 conceptos → 5 procedimientos.
   Muestra el hallazgo de que *normativa* y *clima* no tienen procedimiento.
3. **Cómo razona el agente** — su decisión autónoma (evidencia directa vs. estadística),
   con las trazas reales del agente. Dos escenarios: obra 118 y proyecto nuevo.
4. **Red interactiva (tipo Obsidian)**: cada punto es una nota `.md` real de la bóveda
   (40 episodios, 4 semánticas, 5 procedurales) y cada línea es uno de sus 131 `[[wikilinks]]`.
   También se muestran los 6 conceptos de causa con sus 82 relaciones de órdenes de cambio,
   y se pueden activar los `#tags`.

## Red interactiva (vista 4)

Abrir `red-interactiva.html` con doble clic, o pulsar `4` / el botón *4 · Red interactiva* en las otras vistas.

| Acción | Resultado |
|--------|-----------|
| Clic en un punto | Lo selecciona, resalta sus líneas y vecinos y abre su ficha (datos, enlaces, backlinks) |
| Arrastrar un punto | Lo mueve; el resto de la red reacciona como una malla elástica |
| Clic en una ficha de vecino | Salta a esa nota |
| Arrastrar el fondo / rueda | Desplazar / zoom (el texto de los episodios aparece al acercarse) |
| Doble clic | Sobre un punto: acercarse · sobre el fondo: encuadrar todo |
| Clic en la leyenda | Oculta o muestra una memoria |
| `/` · `Esc` | Buscar una nota · quitar la selección |
| `T` · `F` · `R` · `C` · `G` | Tema · encuadrar · reanimar · conceptos on/off · ajustes |
| `1` `2` `3` | Volver a las vistas 1-3 |

En **⚙ Ajustes** se puede colorear los episodios por *causa dominante* o por *riesgo*, resaltar
hasta 2 saltos (obra → causa → procedimiento), mostrar `#tags` y flechas, ajustar las fuerzas y
fijar puntos al soltarlos (como en Obsidian). La selección queda en la URL
(`?select=obra-118`), así que se puede abrir directamente en una nota concreta.

## Usar en vivo

Abrir `grafo-memorias.html` con doble clic (Chrome o Edge). Controles:

| Tecla | Acción |
|-------|--------|
| `1` `2` `3` o `←` `→` | Cambiar de vista (sirve el clicker de presentaciones) |
| `4` | Abrir la red interactiva tipo Obsidian |
| `T` | Tema oscuro / claro |
| `S` | Escenario de la vista 3 (directa / estadística) |
| `P` o espacio | Reproducir el recorrido del agente paso a paso |
| Pasar el cursor | Resalta la ruta completa de una obra, causa o procedimiento |
| Rueda / arrastrar / doble clic | Zoom / mover / restablecer |

La barra de controles se oculta sola y reaparece al mover el ratón. Con internet usa la
tipografía Manrope; sin conexión cae a Segoe UI sin romper nada.

## Regenerar (si cambian las memorias)

```powershell
cd DESVIAI_TFM
backend\.venv\Scripts\python.exe presentacion\grafos\build_data.py
presentacion\grafos\exportar_png.ps1          # -Scale 1 para 1920x1080
```
