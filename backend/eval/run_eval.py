"""
run_eval.py — Evaluación del agente con 5 casos canónicos (exigencia del mentor).

Cada caso comprueba una capacidad distinta del agente. La VERDAD DE REFERENCIA se
deriva de los datos y artefactos reales (SHAP, dataset, memoria episódica), no de
valores fijados a mano: el test verifica que el agente cite exactamente esos valores.

Como el modo mock es determinístico, la evaluación es 100% reproducible sin API key.
(Si AGENT_MODE=claude, evalúa al agente real con las mismas comprobaciones.)

Métricas:
  - Precisión de invocación de tools   (¿llamó las herramientas correctas?)
  - Exactitud factual                  (¿los números/causas citados == la fuente?)
  - Cobertura de citación              (¿declara la fuente de cada afirmación?)
  - Ruta de evidencia                  (¿directa vs. estadística según corresponde?)
  - Precisión de recuperación          (¿trae el documento de memoria correcto?)

Uso:  python eval/run_eval.py     (desde backend/)
"""
from __future__ import annotations
import os, sys, json, re
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django  # noqa: E402
django.setup()

import joblib  # noqa: E402
from core.agent import service  # noqa: E402
from core.agent.mock import CATEGORIA_NOMBRE  # noqa: E402
from core.ml import explainer  # noqa: E402
from core import memory  # noqa: E402

ART = BASE / 'core' / 'ml' / 'artifacts'
OUT = Path(__file__).resolve().parent


# --- utilidades --------------------------------------------------------------

def project_from_row(row) -> dict:
    return {
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


def contiene(texto: str, *subs, ci=True) -> bool:
    t = texto.lower() if ci else texto
    return all((s.lower() if ci else s) in t for s in subs)


def num_en(texto: str, val: float) -> bool:
    """¿Aparece el número `val`? Exige decimal o entero seguido de % para evitar
    falsos positivos con cifras sueltas (p.ej. '14 niveles')."""
    for fmt in (f'{val}', f'{val:.1f}', f'{val:.2f}', f'{round(val)}%'):
        if fmt in texto:
            return True
    return False


def tools_invocadas(res) -> list:
    return [t['tool'] for t in res['trazabilidad']]


def trace_de(res, tool):
    return next((t for t in res['trazabilidad'] if t['tool'] == tool), None)


# --- definición de los 5 casos ----------------------------------------------

def construir_casos():
    df = joblib.load(ART / 'dataset_engineered.pkl')
    eps = memory.obras_con_episodio()
    df_ep = df[df['id_proyecto'].isin(eps)]

    # Caso 1: obra CON episodio y mayor desvío (causa clara y documentada).
    r1 = df_ep.sort_values('desvio_costo', ascending=False).iloc[0]
    # Caso 4: obra CON episodio y riesgo BAJO (qué se hizo bien).
    r4 = df_ep[df_ep['desvio_costo_alto'] == 0].sort_values('desvio_costo').iloc[0]
    # Caso 3: obra riesgo ALTO SIN episodio (drivers SHAP, sin evidencia forense).
    df_alto_sin_ep = df[(df['desvio_costo_alto'] == 1) & (~df['id_proyecto'].isin(eps))]
    r3 = df_alto_sin_ep.sort_values('desvio_costo', ascending=False).iloc[0]

    # Caso 2 y 5: proyecto nuevo (sin id histórico).
    nuevo = {
        'sup_m2': 45000, 'niveles': 35, 'unidades': 400,
        'presupuesto_inicial': 30_000_000, 'tiempo_inicial': 730,
        'sistema_constructivo': 'Concreto Postensado', 'nivel_acabado': 'Medio',
        'avance_proyecto': '70 - 80', 'proyectos_similares': '10 - 15', 'fecha_inicio': '2024-03',
    }

    casos = [
        {'id': 1, 'nombre': 'Obra CON episodio — ¿por qué se desvió?',
         'project': project_from_row(r1), 'obra_id': int(r1['id_proyecto']),
         'pregunta': '¿Por qué se desvió esta obra?', 'gt_row': r1},
        {'id': 2, 'nombre': 'Proyecto SIN episodio — ¿qué explica el riesgo?',
         'project': nuevo, 'obra_id': None,
         'pregunta': '¿Qué explica el riesgo de este proyecto?'},
        {'id': 3, 'nombre': 'Riesgo ALTO — drivers estructurales (SHAP)',
         'project': project_from_row(r3), 'obra_id': None,
         'pregunta': '¿Qué explica el riesgo alto de este proyecto?'},
        {'id': 4, 'nombre': 'Riesgo BAJO — ¿qué se hizo bien?',
         'project': project_from_row(r4), 'obra_id': int(r4['id_proyecto']),
         'pregunta': '¿Qué se hizo bien en esta obra?', 'gt_row': r4},
        {'id': 5, 'nombre': 'Mitigación de cambio de alcance (recuperación)',
         'project': nuevo, 'obra_id': None,
         'pregunta': '¿Cómo mitigo el riesgo de cambio de alcance?'},
    ]
    return casos


# --- comprobaciones por caso -------------------------------------------------

def checks_caso(caso, res):
    """Devuelve lista de checks: (tipo, nombre, ok, detalle)."""
    resp = res['respuesta']
    tools = tools_invocadas(res)
    C = []

    if caso['id'] == 1:
        ep = memory.get_episodio(caso['obra_id'])
        desvio = ep['meta']['desvio_costo_real']
        causa = CATEGORIA_NOMBRE.get(ep['meta']['causa_dominante'], ep['meta']['causa_dominante'])
        C += [
            ('tool', 'invoca consultar_shap y buscar_episodio',
             {'consultar_shap', 'buscar_episodio'} <= set(tools), ''),
            ('evidencia', 'usa evidencia DIRECTA', contiene(resp, 'directa'), ''),
            ('factual', f'cita el desvío real ({desvio}%)', num_en(resp, desvio), ''),
            ('factual', f'cita la causa dominante ({causa})', contiene(resp, causa), ''),
            ('citacion', 'declara la fuente', contiene(resp, 'fuente'), ''),
        ]
    elif caso['id'] == 2:
        C += [
            ('tool', 'invoca SHAP + episodio + similares',
             {'consultar_shap', 'buscar_episodio', 'buscar_casos_similares'} <= set(tools), ''),
            ('evidencia', 'declara inferencia ESTADÍSTICA', contiene(resp, 'estad'), ''),
            ('evidencia', 'aclara que NO es evidencia directa',
             contiene(resp, 'no', 'evidencia directa') or contiene(resp, 'no hay'), ''),
            ('citacion', 'declara la fuente', contiene(resp, 'fuente'), ''),
        ]
    elif caso['id'] == 3:
        exp = explainer.explicar_local(caso['project'], 'desvio_costo')
        top = next(c for c in exp['contribuciones'] if c['sentido'] == 'sube')
        C += [
            ('tool', 'invoca consultar_shap', 'consultar_shap' in tools, ''),
            ('factual', f"cita el driver SHAP top ('{top['variable']}')",
             contiene(resp, top['variable']), ''),
            ('factual', f"cita la predicción ({exp['prediccion_pct']}%)",
             num_en(resp, exp['prediccion_pct']), ''),
            ('citacion', 'declara la capa/fuente', contiene(resp, 'capa') or contiene(resp, 'fuente'), ''),
        ]
    elif caso['id'] == 4:
        exp = explainer.explicar_local(caso['project'], 'desvio_costo')
        protect = next((c for c in exp['contribuciones'] if c['sentido'] == 'baja'), None)
        C += [
            ('intent', "clasifica intención 'qué se hizo bien'", res.get('intent') == 'que_bien', ''),
            ('tool', 'invoca consultar_shap', 'consultar_shap' in tools, ''),
            ('factual', 'cita un factor protector (SHAP negativo)',
             bool(protect) and contiene(resp, protect['variable']), ''),
            ('citacion', 'declara la fuente', contiene(resp, 'fuente') or contiene(resp, 'capa'), ''),
        ]
    elif caso['id'] == 5:
        lm = trace_de(res, 'leer_memoria')
        C += [
            ('intent', "clasifica intención 'mitigación'", res.get('intent') == 'mitigacion', ''),
            ('tool', 'invoca leer_memoria', 'leer_memoria' in tools, ''),
            ('retrieval', 'recupera el procedimiento de ALCANCE',
             bool(lm) and 'mitigacion-cambio-alcance' in lm['resumen'], ''),
            ('citacion', 'declara la fuente', contiene(resp, 'fuente'), ''),
        ]
    return C


METRICA_DE_TIPO = {
    'tool': 'Precisión de invocación de tools',
    'factual': 'Exactitud factual',
    'citacion': 'Cobertura de citación',
    'evidencia': 'Ruta de evidencia',
    'retrieval': 'Precisión de recuperación',
    'intent': 'Clasificación de intención',
}


def main():
    casos = construir_casos()
    resultados, ag_por_tipo = [], {}

    print('=' * 78)
    print(' EVALUACIÓN DEL AGENTE — 5 CASOS CANÓNICOS')
    print('=' * 78)

    for caso in casos:
        res = service.run_agent(caso['project'], obra_id=caso['obra_id'], pregunta=caso['pregunta'])
        checks = checks_caso(caso, res)
        ok_caso = sum(1 for _, _, ok, _ in checks if ok)
        print(f"\n[Caso {caso['id']}] {caso['nombre']}")
        print(f"  Q: {caso['pregunta']}  ·  obra_id={caso['obra_id']}  ·  modo={res['modo']}")
        print(f"  tools: {' → '.join(tools_invocadas(res))}")
        for tipo, nombre, ok, _ in checks:
            print(f"    [{'✓' if ok else '✗'}] {nombre}")
            agg = ag_por_tipo.setdefault(tipo, [0, 0])
            agg[0] += int(ok); agg[1] += 1
        resultados.append({
            'id': caso['id'], 'nombre': caso['nombre'], 'pregunta': caso['pregunta'],
            'obra_id': caso['obra_id'], 'modo': res['modo'], 'intent': res.get('intent'),
            'tools': tools_invocadas(res),
            'checks': [{'tipo': t, 'nombre': n, 'ok': ok} for t, n, ok, _ in checks],
            'ok': ok_caso, 'total': len(checks),
            'respuesta': res['respuesta'],
        })

    # --- métricas agregadas --------------------------------------------------
    print('\n' + '=' * 78)
    print(' MÉTRICAS AGREGADAS')
    print('=' * 78)
    metricas = {}
    for tipo, (ok, tot) in agg_ordenado(ag_por_tipo):
        pct = round(ok / tot * 100, 1)
        metricas[METRICA_DE_TIPO.get(tipo, tipo)] = {'aciertos': ok, 'total': tot, 'pct': pct}
        print(f"  {METRICA_DE_TIPO.get(tipo, tipo):36s} {ok}/{tot}  ({pct:.0f}%)")

    total_ok = sum(r['ok'] for r in resultados)
    total_ch = sum(r['total'] for r in resultados)
    global_pct = round(total_ok / total_ch * 100, 1)
    print(f"\n  {'GLOBAL (todos los checks)':36s} {total_ok}/{total_ch}  ({global_pct:.0f}%)")

    salida = {'casos': resultados, 'metricas': metricas,
              'global': {'aciertos': total_ok, 'total': total_ch, 'pct': global_pct}}
    (OUT / 'resultados.json').write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding='utf-8')
    _escribir_md(salida)
    print(f"\n✅ Resultados en {OUT / 'resultados.json'} y resultados.md")


def agg_ordenado(agg):
    orden = ['tool', 'factual', 'citacion', 'evidencia', 'retrieval', 'intent']
    return [(t, agg[t]) for t in orden if t in agg]


def _escribir_md(salida):
    L = ['# Evaluación del agente — 5 casos canónicos', '',
         '## Métricas agregadas', '',
         '| Métrica | Aciertos | % |', '|---|---|---|']
    for nombre, m in salida['metricas'].items():
        L.append(f"| {nombre} | {m['aciertos']}/{m['total']} | {m['pct']:.0f}% |")
    g = salida['global']
    L.append(f"| **Global** | **{g['aciertos']}/{g['total']}** | **{g['pct']:.0f}%** |")
    L += ['', '## Detalle por caso', '']
    for c in salida['casos']:
        L.append(f"### Caso {c['id']} — {c['nombre']}")
        L.append(f"- **Pregunta:** {c['pregunta']}  ·  obra_id: {c['obra_id']}  ·  modo: {c['modo']}")
        L.append(f"- **Tools:** {' → '.join(c['tools'])}")
        L.append(f"- **Checks:** {c['ok']}/{c['total']}")
        for ch in c['checks']:
            L.append(f"  - [{'x' if ch['ok'] else ' '}] {ch['nombre']}")
        L.append(f"- **Respuesta:**\n\n  > {c['respuesta'].replace(chr(10), chr(10)+'  > ')}")
        L.append('')
    (OUT / 'resultados.md').write_text('\n'.join(L), encoding='utf-8')


if __name__ == '__main__':
    main()
