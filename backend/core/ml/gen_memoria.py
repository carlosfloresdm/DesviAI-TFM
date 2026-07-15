"""
gen_memoria.py — Genera la capa forense (órdenes de cambio) y la memoria episódica.

Para un subconjunto (~20%) del histórico reconstruye órdenes de cambio sintéticas
COHERENTES: la suma de sus impactos de costo cuadra exactamente con la brecha real
(presupuesto_final - presupuesto_inicial) de cada obra, y la de plazo con
(tiempo_final - tiempo_inicial). Cada obra produce:
  - filas en core/data/ordenes_cambio.csv (capa 3)
  - un archivo knowledge/episodica/obra-XXX.md (memoria episódica)

Además calcula la tabla de atribución agregada por categoría de causa.

Declarado como ESTUDIO PILOTO reconstruido (ver propuesta técnica): el subconjunto
con evidencia forense es una calibración, no base de conclusiones generalizables.

Uso:  python core/ml/gen_memoria.py     (desde backend/)
Determinístico (semilla por obra) -> reproducible.
"""
from __future__ import annotations
import sys, csv, json, unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import predictor  # noqa: E402

ART = BASE / 'artifacts'
DATA = BASE.parent / 'data'
REPO = BASE.parents[2]
KNOWLEDGE = REPO / 'knowledge'
EPISODICA = KNOWLEDGE / 'episodica'

SEED = 42
PCT_SUBCONJUNTO = 0.20  # 20% del histórico con órdenes reconstruidas (rango 10-30%)

# --- Categorías de causa (idénticas a la propuesta técnica) ------------------
# w_costo / w_plazo = peso relativo con que cada causa contribuye a cada brecha.
CATEGORIAS = {
    'alcance': {
        'nombre': 'Cambio de alcance', 'w_costo': 0.30, 'w_plazo': 0.16,
        'partidas': ['estructura', 'acabados', 'urbanización', 'instalaciones eléctricas'],
        'plantillas': [
            'Ampliación de {partida} solicitada por el cliente respecto al proyecto original.',
            'Incorporación de nuevos requerimientos en {partida} no contemplados en el contrato inicial.',
        ],
    },
    'diseño': {
        'nombre': 'Error u omisión de diseño', 'w_costo': 0.25, 'w_plazo': 0.15,
        'partidas': ['columnas', 'losas', 'cimentación', 'instalaciones hidrosanitarias'],
        'plantillas': [
            'Rediseño de {partida} por interferencias detectadas en obra.',
            'Corrección de omisión en planos de {partida} que obligó a rehacer trabajo ejecutado.',
        ],
    },
    'proveedor': {
        'nombre': 'Proveedor / suministro', 'w_costo': 0.18, 'w_plazo': 0.25,
        'partidas': ['estructura', 'fachada', 'ascensores', 'acabados'],
        'plantillas': [
            'Incremento de precio del suministro de {partida} frente a la cotización inicial.',
            'Retraso en la entrega de materiales de {partida} que encareció la partida.',
        ],
    },
    'sitio': {
        'nombre': 'Condición de sitio imprevista', 'w_costo': 0.15, 'w_plazo': 0.22,
        'partidas': ['cimentación', 'movimiento de tierras', 'urbanización'],
        'plantillas': [
            'Condición del terreno distinta a la esperada en {partida} (nivel freático / roca).',
            'Sobreexcavación y refuerzo imprevistos en {partida}.',
        ],
    },
    'normativa': {
        'nombre': 'Ajuste normativo', 'w_costo': 0.08, 'w_plazo': 0.12,
        'partidas': ['instalaciones eléctricas', 'estructura', 'impermeabilización'],
        'plantillas': [
            'Adecuación de {partida} a exigencia normativa surgida durante la ejecución.',
            'Requisito adicional de la autoridad para {partida} en la revisión de permisos.',
        ],
    },
    'clima': {
        'nombre': 'Clima', 'w_costo': 0.04, 'w_plazo': 0.10,
        'partidas': ['movimiento de tierras', 'impermeabilización', 'fachada'],
        'plantillas': [
            'Paralización por lluvias que afectó {partida} y requirió trabajos de recuperación.',
            'Daños por condiciones climáticas adversas en {partida}.',
        ],
    },
}


def slug(texto: str) -> str:
    """Normaliza para tags/nombres (sin tildes, minúsculas)."""
    t = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode()
    return t.lower().replace(' ', '-')


def n_ordenes(desvio_costo: float) -> int:
    if desvio_costo < 3:
        return 1
    if desvio_costo < 6:
        return 2
    if desvio_costo < 10:
        return 3
    return 4


def split_entero(total: int, pesos, rng) -> list[int]:
    """Reparte `total` (entero) proporcional a `pesos`, sumando exactamente total."""
    w = np.array(pesos, dtype=float)
    if w.sum() == 0 or total == 0:
        return [0] * len(pesos)
    w = w / w.sum()
    raw = w * total
    parts = np.floor(raw).astype(int)
    resto = int(total - parts.sum())
    orden = np.argsort(-(raw - parts))  # a quienes tienen mayor parte fraccionaria
    for i in range(resto):
        parts[orden[i % len(parts)]] += 1
    return parts.tolist()


def generar():
    df = joblib.load(ART / 'dataset_engineered.pkl')
    ids = sorted(df['id_proyecto'].astype(int).tolist())
    n_sel = round(len(ids) * PCT_SUBCONJUNTO)
    rng_sel = np.random.default_rng(SEED)
    seleccion = sorted(rng_sel.choice(ids, size=n_sel, replace=False).tolist())

    EPISODICA.mkdir(parents=True, exist_ok=True)
    filas_csv = []
    agg = {c: {'monto': 0, 'n': 0} for c in CATEGORIAS}
    total_sobrecosto = 0

    for obra_id in seleccion:
        row = df[df['id_proyecto'] == obra_id].iloc[0]
        gap_costo = int(row['presupuesto_final'] - row['presupuesto_inicial'])
        gap_plazo = int(row['tiempo_final'] - row['tiempo_inicial'])
        rng = np.random.default_rng(1000 + obra_id)

        n = n_ordenes(float(row['desvio_costo']))
        cats = list(CATEGORIAS)
        p = np.array([CATEGORIAS[c]['w_costo'] for c in cats])
        p = p / p.sum()
        elegidas = list(rng.choice(cats, size=min(n, len(cats)), replace=False, p=p))

        # Reparto coherente del sobrecosto y del sobreplazo entre las órdenes.
        pesos_costo = [CATEGORIAS[c]['w_costo'] * (0.8 + 0.4 * rng.random()) for c in elegidas]
        pesos_plazo = [CATEGORIAS[c]['w_plazo'] * (0.8 + 0.4 * rng.random()) for c in elegidas]
        montos = split_entero(gap_costo, pesos_costo, rng)
        plazos = split_entero(gap_plazo, pesos_plazo, rng)

        # Fechas dentro del periodo de obra (20%-90% del avance).
        fracs = sorted(0.2 + 0.7 * rng.random(len(elegidas)))
        fecha_ini = pd.Timestamp(row['fecha_inicio'])

        ordenes_obra = []
        for j, cat in enumerate(elegidas):
            meta = CATEGORIAS[cat]
            partida = str(rng.choice(meta['partidas']))
            plantilla = str(rng.choice(meta['plantillas']))
            fecha = (fecha_ini + pd.Timedelta(days=int(fracs[j] * row['tiempo_inicial']))).date()
            oc = {
                'proyecto_id': obra_id,
                'orden_id': f'OC-{obra_id:03d}-{j+1}',
                'fecha': fecha.isoformat(),
                'categoria': cat,
                'categoria_nombre': meta['nombre'],
                'partida_afectada': partida,
                'impacto_costo': int(montos[j]),
                'impacto_plazo_dias': int(plazos[j]),
                'descripcion': plantilla.format(partida=partida),
            }
            ordenes_obra.append(oc)
            filas_csv.append(oc)
            agg[cat]['monto'] += int(montos[j])
            agg[cat]['n'] += 1
        total_sobrecosto += gap_costo

        _escribir_episodio(row, ordenes_obra, gap_costo, gap_plazo)

    # --- CSV de órdenes de cambio -------------------------------------------
    DATA.mkdir(parents=True, exist_ok=True)
    campos = ['proyecto_id', 'orden_id', 'fecha', 'categoria', 'categoria_nombre',
              'partida_afectada', 'impacto_costo', 'impacto_plazo_dias', 'descripcion']
    with open(DATA / 'ordenes_cambio.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas_csv)

    # --- Atribución agregada por categoría ----------------------------------
    por_cat = {}
    for c, d in sorted(agg.items(), key=lambda x: -x[1]['monto']):
        por_cat[c] = {
            'nombre': CATEGORIAS[c]['nombre'],
            'monto_usd': d['monto'], 'n_ordenes': d['n'],
            'pct_del_sobrecosto': round(d['monto'] / total_sobrecosto * 100, 1) if total_sobrecosto else 0,
        }
    atribucion = {
        'n_obras_con_episodio': len(seleccion),
        'pct_del_historico': round(len(seleccion) / len(ids) * 100, 1),
        'total_sobrecosto_usd': total_sobrecosto,
        'n_ordenes_total': len(filas_csv),
        'por_categoria': por_cat,
        'nota': ('Estudio piloto: órdenes de cambio reconstruidas para el '
                 f'{round(len(seleccion) / len(ids) * 100)}% del histórico. Calibración '
                 'forense, no base de conclusiones generalizables al 100% de las obras.'),
    }
    (KNOWLEDGE / 'atribucion_agregada.json').write_text(
        json.dumps(atribucion, ensure_ascii=False, indent=2), encoding='utf-8')

    # --- Resumen -------------------------------------------------------------
    print(f'Obras con episodio: {len(seleccion)} ({atribucion["pct_del_historico"]}% del histórico)')
    print(f'Órdenes de cambio generadas: {len(filas_csv)}')
    print(f'Sobrecosto total reconstruido: ${total_sobrecosto:,} USD')
    print('\nAtribución agregada por categoría:')
    for c, d in por_cat.items():
        print(f'  {d["nombre"]:32s} {d["pct_del_sobrecosto"]:5.1f}%  (${d["monto_usd"]:>12,}  ·  {d["n_ordenes"]} OC)')
    print(f'\nEpisodios .md escritos en: {EPISODICA}')
    print(f'Órdenes CSV: {DATA / "ordenes_cambio.csv"}')
    print(f'Atribución agregada: {KNOWLEDGE / "atribucion_agregada.json"}')


def _escribir_episodio(row, ordenes, gap_costo, gap_plazo):
    """Escribe knowledge/episodica/obra-XXX.md."""
    obra_id = int(row['id_proyecto'])
    tipologia = row['sistema_constructivo']
    cats = list(dict.fromkeys(o['categoria'] for o in ordenes))
    cat_dom = max(ordenes, key=lambda o: o['impacto_costo'])['categoria']

    # Estimación del modelo (in-sample, sólo ilustrativa en el episodio).
    proyecto = {
        'sup_m2': int(row['sup_m2']), 'niveles': int(row['niveles']),
        'unidades': int(row['unidades']),
        'presupuesto_inicial': int(row['presupuesto_inicial']),
        'tiempo_inicial': int(row['tiempo_inicial']),
        'sistema_constructivo': row['sistema_constructivo'],
        'nivel_acabado': row['nivel_acabado'],
        'avance_proyecto': row['avance_proyecto'],
        'proyectos_similares': row['proyectos_similares'],
        'fecha_inicio': str(row['periodo_inicio']),
    }
    pred = predictor.predecir_proyecto(proyecto)
    pc, pt = pred['costo'], pred['tiempo']

    riesgo_costo = 'ALTO' if int(row['desvio_costo_alto']) else 'BAJO'
    riesgo_tiempo = 'ALTO' if int(row['desvio_tiempo_alto']) else 'BAJO'

    # Relaciones (wikilinks) según categorías presentes.
    mapa_mitig = {
        'alcance': 'mitigacion-cambio-alcance', 'diseño': 'mitigacion-error-diseno',
        'sitio': 'mitigacion-condicion-sitio', 'proveedor': 'mitigacion-proveedores',
    }
    relacionados = [mapa_mitig[c] for c in cats if c in mapa_mitig] + ['causas-de-desvio']

    tags = [slug(tipologia)] + [slug(c) for c in cats]
    if riesgo_costo == 'ALTO':
        tags.append('desviacion-alta')

    # Tabla de órdenes
    filas = '\n'.join(
        f"| {o['fecha']} | {o['categoria_nombre']} | {o['partida_afectada']} | "
        f"${o['impacto_costo']:,} | {o['impacto_plazo_dias']} d | {o['descripcion']} |"
        for o in ordenes)

    # Atribución por categoría dentro de la obra
    atrib = {}
    for o in ordenes:
        atrib.setdefault(o['categoria'], 0)
        atrib[o['categoria']] += o['impacto_costo']
    atrib_txt = '\n'.join(
        f"- **{CATEGORIAS[c]['nombre']}**: {round(m / gap_costo * 100)}% del sobrecosto "
        f"(${m:,})" for c, m in sorted(atrib.items(), key=lambda x: -x[1]))

    contenido = f"""---
tipo: episodio
obra_id: {obra_id}
tipologia: {tipologia}
nivel_acabado: {row['nivel_acabado']}
categorias_causa: [{', '.join(cats)}]
causa_dominante: {cat_dom}
desvio_costo_real: {round(float(row['desvio_costo']), 2)}
desvio_tiempo_real: {round(float(row['desvio_tiempo']), 2)}
riesgo_costo: {riesgo_costo}
riesgo_tiempo: {riesgo_tiempo}
tags: [{', '.join(dict.fromkeys(tags))}]
relacionados: [{', '.join(dict.fromkeys(relacionados))}]
---

# Obra {obra_id:03d} — {tipologia}, acabado {row['nivel_acabado']}

Proyecto de {int(row['sup_m2']):,} m², {int(row['niveles'])} niveles, {int(row['unidades'])} unidades.
Inicio: {row['periodo_inicio']} · Presupuesto inicial: ${int(row['presupuesto_inicial']):,} USD.

## Qué se predijo vs. qué pasó

| | Modelo (estimación) | Real |
|---|---|---|
| Desvío de costo | {pc['desvio_estimado_pct']}% ({pc['riesgo']}) | **{round(float(row['desvio_costo']), 2)}%** |
| Desvío de plazo | {pt['desvio_estimado_pct']}% ({pt['riesgo']}) | **{round(float(row['desvio_tiempo']), 2)}%** |
| Presupuesto final | ${pc['presupuesto_final_est']:,} | **${int(row['presupuesto_final']):,}** |

Sobrecosto real: **${gap_costo:,} USD** · Sobreplazo real: **{gap_plazo} días**.

## Órdenes de cambio reconstruidas

| Fecha | Categoría | Partida | Impacto costo | Impacto plazo | Descripción |
|---|---|---|---|---|---|
{filas}

## Atribución del sobrecosto por causa

{atrib_txt}

## Lección aprendida

La causa dominante de esta obra fue **{CATEGORIAS[cat_dom]['nombre'].lower()}**. Ver
procedimientos de mitigación en {', '.join('[[' + r + ']]' for r in dict.fromkeys(relacionados))}.
"""
    (EPISODICA / f'obra-{obra_id:03d}.md').write_text(contenido, encoding='utf-8')


if __name__ == '__main__':
    generar()
