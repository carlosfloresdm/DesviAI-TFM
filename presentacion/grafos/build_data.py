"""
build_data.py — Genera los datos del grafo de memorias a partir de la base de
conocimiento REAL (knowledge/*.md + órdenes de cambio) y los inyecta en
grafo-memorias.html.

Nada está escrito a mano: nodos, aristas y pesos salen de las memorias
episódica, semántica y procedural, y las trazas de la vista 3 salen de ejecutar
el agente real (modo mock).

Uso (desde la raíz del repo):
    backend\\.venv\\Scripts\\python.exe presentacion\\grafos\\build_data.py
"""
from __future__ import annotations
import csv, json, re, sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
KNOW = REPO / 'knowledge'
sys.path.insert(0, str(REPO / 'backend'))

import joblib  # noqa: E402
from core import memory  # noqa: E402
from core.agent import tools as T, mock  # noqa: E402

HTMLS = [HERE / 'grafo-memorias.html', HERE / 'red-interactiva.html']   # páginas que reciben los datos
NARRATIVA = [118, 177, 167]          # las 3 obras que eligió el equipo

CAUSAS = {  # id -> nombre corto (el orden fija la posición en los grafos)
    'diseño': 'Error / omisión de diseño',
    'alcance': 'Cambio de alcance',
    'proveedor': 'Proveedor / suministro',
    'sitio': 'Condición de sitio',
    'normativa': 'Ajuste normativo',
    'clima': 'Clima',
}


def pasos_de(body: str, n: int = 4) -> list[str]:
    """Primeros n puntos numerados de un procedimiento (une líneas envueltas)."""
    items, cur = [], None
    for line in body.splitlines():
        m = re.match(r'^\d+\.\s+(.*)', line)
        if m:
            if cur:
                items.append(cur)
            cur = m.group(1).strip()
        elif cur is not None:
            s = line.strip()
            if not s or s.startswith('#'):
                items.append(cur)
                cur = None
            else:
                cur += ' ' + s
    if cur:
        items.append(cur)
    out = []
    for it in items[:n]:
        titulo = re.search(r'\*\*(.+?)\*\*', it)
        out.append(titulo.group(1) if titulo else re.sub(r'\s+', ' ', it)[:60])
    return out


def extracto(body: str, n: int = 300) -> str:
    """Primeras frases legibles de una nota (sin títulos, tablas ni marcas markdown)."""
    partes = []
    for ln in body.splitlines():
        s = ln.strip()
        if not s or s.startswith(('#', '|', '>', '- [')):
            continue
        s = re.sub(r'\[\[([^\]]+)\]\]', r'\1', s)
        s = re.sub(r'\*\*(.+?)\*\*', r'\1', s).replace('`', '')
        partes.append(s.lstrip('- '))
        if sum(len(p) for p in partes) > n:
            break
    t = ' '.join(partes)
    return (t[:n].rsplit(' ', 1)[0] + '…') if len(t) > n else t


def definiciones_causas() -> dict:
    """Lee la tabla de definiciones de la memoria semántica causas-de-desvio.md."""
    doc = memory.get_doc('causas-de-desvio')
    defs = {}
    mapa = {'Cambio de alcance': 'alcance', 'Error u omisión de diseño': 'diseño',
            'Condición de sitio imprevista': 'sitio', 'Ajuste normativo': 'normativa',
            'Proveedor / suministro': 'proveedor', 'Clima': 'clima'}
    for m in re.finditer(r'^\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|', doc['body'], flags=re.M):
        if m.group(1) in mapa:
            defs[mapa[m.group(1)]] = m.group(2).strip()
    return defs


def main():
    memory.reload()
    episodios = {oid: memory.get_episodio(oid) for oid in sorted(memory.obras_con_episodio())}

    # --- Órdenes de cambio: impacto por obra y categoría ---------------------
    por_obra = defaultdict(lambda: defaultdict(lambda: {'costo': 0, 'plazo': 0, 'n': 0}))
    with open(REPO / 'backend' / 'core' / 'data' / 'ordenes_cambio.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            d = por_obra[int(r['proyecto_id'])][r['categoria']]
            d['costo'] += int(r['impacto_costo'])
            d['plazo'] += int(r['impacto_plazo_dias'])
            d['n'] += 1

    # --- Memoria episódica: una ficha por obra --------------------------------
    obras, aristas_oc = [], []
    for oid, doc in episodios.items():
        m = doc['meta']
        cats = por_obra[oid]
        total_c = sum(v['costo'] for v in cats.values()) or 1
        obras.append({
            'id': f'obra-{oid}', 'num': oid, 'tipo': 'obra',
            'tipologia': m.get('tipologia'), 'acabado': m.get('nivel_acabado'),
            'costo': m.get('desvio_costo_real'), 'plazo': m.get('desvio_tiempo_real'),
            'riesgo': m.get('riesgo_costo'), 'dominante': m.get('causa_dominante'),
            'n_oc': sum(v['n'] for v in cats.values()),
            'sobrecosto': total_c,
        })
        for cat, v in cats.items():
            aristas_oc.append({
                'from': f'obra-{oid}', 'to': f'causa-{cat}', 'rel': 'PRESENTÓ',
                'pct': round(v['costo'] / total_c * 100, 1),
                'dominante': cat == m.get('causa_dominante'),
                'n_oc': v['n'],
            })

    # --- Memoria semántica: causas y efectos ----------------------------------
    atrib = json.loads((KNOW / 'atribucion_agregada.json').read_text(encoding='utf-8'))
    defs = definiciones_causas()
    tot_costo = defaultdict(int)
    tot_plazo = defaultdict(int)
    for cats in por_obra.values():
        for cat, v in cats.items():
            tot_costo[cat] += v['costo']
            tot_plazo[cat] += v['plazo']
    sum_c, sum_p = sum(tot_costo.values()) or 1, sum(tot_plazo.values()) or 1

    causas = []
    for cid, nombre in CAUSAS.items():
        causas.append({
            'id': f'causa-{cid}', 'key': cid, 'tipo': 'causa', 'nombre': nombre,
            'definicion': defs.get(cid, ''),
            'pct_costo': round(tot_costo[cid] / sum_c * 100, 1),
            'pct_plazo': round(tot_plazo[cid] / sum_p * 100, 1),
            'n_obras': sum(1 for e in aristas_oc if e['to'] == f'causa-{cid}'),
            'n_dominante': sum(1 for o in obras if o['dominante'] == cid),
            'fuente': 'semantica/causas-de-desvio.md',
        })
    efectos = [
        {'id': 'efecto-costo', 'tipo': 'efecto', 'nombre': 'Sobrecosto',
         'total': atrib['total_sobrecosto_usd'], 'fuente': 'semantica/causas-de-desvio.md'},
        {'id': 'efecto-plazo', 'tipo': 'efecto', 'nombre': 'Sobreplazo',
         'total': sum_p, 'fuente': 'semantica/causas-de-desvio.md'},
    ]
    aristas_ce = []
    for c in causas:
        aristas_ce.append({'from': c['id'], 'to': 'efecto-costo', 'rel': 'CONTRIBUYE A', 'pct': c['pct_costo']})
        aristas_ce.append({'from': c['id'], 'to': 'efecto-plazo', 'rel': 'CONTRIBUYE A', 'pct': c['pct_plazo']})

    # --- Memoria procedural: mitigaciones + checklist -------------------------
    mitig, aristas_cm, aristas_chk = [], [], []
    for doc in memory.list_by(memoria='procedural'):
        meta = doc['meta']
        nodo = {'id': f"proc-{doc['name']}", 'tipo': 'checklist' if 'checklist' in doc['name'] else 'mitigacion',
                'nombre': meta.get('titulo', doc['name']), 'causa': meta.get('causa'),
                'pasos': pasos_de(doc['body']), 'fuente': f"procedural/{doc['name']}.md",
                'links': memory.wikilinks(doc['body'])}
        mitig.append(nodo)
        if nodo['causa']:
            aristas_cm.append({'from': f"causa-{nodo['causa']}", 'to': nodo['id'], 'rel': 'SE MITIGA CON'})
    chk = next(n for n in mitig if n['tipo'] == 'checklist')
    for n in mitig:
        if n['tipo'] == 'mitigacion' and n['id'].replace('proc-', '') in chk['links']:
            aristas_chk.append({'from': chk['id'], 'to': n['id'], 'rel': 'INCLUYE'})
    sin_proc = [c['key'] for c in causas if not any(e['from'] == c['id'] for e in aristas_cm)]

    # --- Vista 3: trazas REALES del agente ------------------------------------
    df = joblib.load(REPO / 'backend' / 'core' / 'ml' / 'artifacts' / 'dataset_engineered.pkl')

    def proyecto(oid, fecha=None):
        r = df[df['id_proyecto'] == oid].iloc[0]
        return {'sup_m2': int(r['sup_m2']), 'niveles': int(r['niveles']), 'unidades': int(r['unidades']),
                'presupuesto_inicial': int(r['presupuesto_inicial']), 'tiempo_inicial': int(r['tiempo_inicial']),
                'sistema_constructivo': r['sistema_constructivo'], 'nivel_acabado': r['nivel_acabado'],
                'avance_proyecto': r['avance_proyecto'], 'proyectos_similares': r['proyectos_similares'],
                'fecha_inicio': fecha or str(r['periodo_inicio'])}

    def corre(ctx, pregunta):
        res = mock.run_mock(ctx, pregunta)
        return {'pregunta': pregunta, 'traza': res['trazabilidad'], 'respuesta': res['respuesta']}

    ctx_a = T.AgentContext(proyecto(118), obra_id=118)
    # Proyecto nuevo (sin historial): parecido a la obra 118 pero más pequeño, para que no sea un clon
    # (el modelo ya no usa la fecha, así que un clon tendría a la propia obra 118 como vecino idéntico)
    nuevo = proyecto(118, fecha='2025-06')
    nuevo.update(sup_m2=round(nuevo['sup_m2'] * .8), niveles=nuevo['niveles'] - 8, unidades=round(nuevo['unidades'] * .8),
                 presupuesto_inicial=round(nuevo['presupuesto_inicial'] * .8, -3))
    ctx_b = T.AgentContext(nuevo, obra_id=None)
    vecinos = T.buscar_casos_similares(ctx_b, k=5)['vecinos']
    escenarios = {
        'directa': {
            'titulo': 'Obra 118 · con episodio documentado',
            'obra': 118,
            'diagnostico': corre(ctx_a, '¿Por qué se desvió esta obra?'),
            'mitigacion': corre(ctx_a, '¿Cómo puedo evitar que vuelva a pasar?'),
        },
        'estadistica': {
            'titulo': 'Proyecto nuevo · sin historial',
            'proyecto': {k: nuevo[k] for k in ('sup_m2', 'niveles', 'sistema_constructivo', 'nivel_acabado')},
            'vecinos': [{'num': v['id_proyecto'], 'costo': v['desvio_costo_real'],
                         'alto': bool(v['desvio_costo_alto']), 'episodio': v['tiene_episodio']} for v in vecinos],
            'diagnostico': corre(ctx_b, '¿Qué explica el riesgo de este proyecto?'),
            'mitigacion': corre(ctx_b, '¿Cómo mitigo el riesgo?'),
        },
    }

    # --- Todas las notas de la bóveda (para la red interactiva tipo Obsidian) ---
    documentos = []
    for doc in memory.list_by():
        m = doc['meta']
        h1 = next((ln[2:].strip() for ln in doc['body'].splitlines() if ln.startswith('# ')), None)
        documentos.append({
            'name': doc['name'], 'memoria': doc['memoria'], 'titulo': m.get('titulo') or h1 or doc['name'],
            'tags': m.get('tags', []), 'links': sorted(set(memory.wikilinks(doc['body']))),
            'extracto': extracto(doc['body']), 'fuente': doc['path'].replace('\\', '/'),
            'obra_id': m.get('obra_id'),
        })
    nombres = {d['name'] for d in documentos}
    sin_resolver = sorted({l for d in documentos for l in d['links'] if l not in nombres})

    data = {
        'documentos': documentos, 'links_sin_resolver': sin_resolver,
        'obras': obras, 'causas': causas, 'efectos': efectos, 'procedural': mitig,
        'aristas': {'obra_causa': aristas_oc, 'causa_efecto': aristas_ce,
                    'causa_mitigacion': aristas_cm, 'checklist': aristas_chk},
        'narrativa': NARRATIVA, 'sin_procedimiento': sin_proc, 'escenarios': escenarios,
        'resumen': {'n_obras': len(obras), 'n_causas': len(causas),
                    'n_procedimientos': len(mitig), 'n_ordenes': atrib['n_ordenes_total'],
                    'n_wikilinks': sum(len(memory.wikilinks(d['body'])) for d in memory.list_by()),
                    'n_docs': memory.resumen()},
    }

    js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    for page in HTMLS:
        if not page.exists():
            continue
        html = page.read_text(encoding='utf-8')
        html, n = re.subn(r'(<script id="graph-data" type="application/json">).*?(</script>)',
                          lambda m: m.group(1) + js + m.group(2), html, flags=re.S)
        if n != 1:
            raise SystemExit(f'No encontré el bloque <script id="graph-data"> en {page.name}')
        page.write_text(html, encoding='utf-8')
        print(f'Datos inyectados en {page.name}')

    print(f'Obras (episódica): {len(obras)} · Causas (semántica): {len(causas)} · '
          f'Procedimientos: {len(mitig)} · Aristas obra→causa: {len(aristas_oc)}')
    print(f'Causas sin procedimiento: {sin_proc}')
    print('Vecinos del proyecto nuevo:', [(v['num'], v['episodio']) for v in escenarios['estadistica']['vecinos']])
    for k, e in escenarios.items():
        for q in ('diagnostico', 'mitigacion'):
            print(f"  [{k}/{q}] " + ' → '.join(t['tool'] for t in e[q]['traza']))
    print(f'Notas en la bóveda: {len(documentos)} · wikilinks sin resolver: {sin_resolver or "ninguno"} · datos {len(js)/1024:.1f} KB')


if __name__ == '__main__':
    main()
