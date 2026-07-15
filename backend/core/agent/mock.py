"""
mock.py — Agente en modo determinístico (sin LLM).

Reproduce la MISMA lógica de decisión que el agente real: clasifica la intención de
la pregunta, invoca las tools pertinentes (registrando la traza) y compone la respuesta
con plantillas alimentadas por datos reales. En particular, aplica la decisión binaria
evidencia-directa vs. evidencia-estadística igual que lo haría el LLM.

Ventaja: la demo y la evaluación son 100% reproducibles y no dependen de una API key.
"""
from __future__ import annotations
import re

from core.agent import tools as T

CATEGORIA_NOMBRE = {
    'alcance': 'cambio de alcance', 'diseño': 'error u omisión de diseño',
    'sitio': 'condición de sitio imprevista', 'proveedor': 'proveedor / suministro',
    'normativa': 'ajuste normativo', 'clima': 'clima',
}
CAUSA_A_TAG = {'alcance': 'alcance', 'diseño': 'diseño', 'sitio': 'sitio', 'proveedor': 'proveedor'}

# Detección de la causa mencionada explícitamente en la pregunta.
CAUSA_KEYWORDS = [
    ('alcance', r'alcance'),
    ('diseño', r'diseñ|diseno'),
    ('sitio', r'sitio|terreno|suelo|geotéc|geotec|subsuelo'),
    ('proveedor', r'proveedor|suministro|material'),
    ('normativa', r'normativ'),
    ('clima', r'clima|lluvia'),
]


def _causa_en_pregunta(pregunta: str):
    q = pregunta.lower()
    for causa, patron in CAUSA_KEYWORDS:
        if re.search(patron, q):
            return causa
    return None


def _clasificar(pregunta: str) -> str:
    q = pregunta.lower()
    if re.search(r'mitig|evitar|reducir|recomend|qué hacer|que hacer|prevenir|cómo mejorar', q):
        return 'mitigacion'
    if re.search(r'confia|fiab|precis|exact|mape|segur|acert', q):
        return 'fiabilidad'
    if re.search(r'similar|comparar|compara|parecid|histó|histo|otras obras', q):
        return 'similares'
    if re.search(r'bien|acierto|fortaleza|protector|favorable|a favor', q):
        return 'que_bien'
    return 'diagnostico'


def _fmt_factores(factores, sentido, n=3):
    sel = [f for f in factores if f['sentido'] == sentido][:n]
    return ', '.join(f"{f['variable']} ({f['contribucion_pts']:+.2f} pts)" for f in sel)


def run_mock(ctx: T.AgentContext, pregunta: str) -> dict:
    trace = []

    def _call(name, **kw):
        out = T.TOOLS[name](ctx, **kw)
        trace.append({'paso': len(trace) + 1, 'tool': name, 'input': kw,
                      'resumen': T.resumen_tool(name, out)})
        return out

    intent = _clasificar(pregunta)

    if intent == 'fiabilidad':
        mem = _call('leer_memoria', tipo='semantica', tags=['bandas'])
        shap = _call('consultar_shap', target='desvio_costo')
        respuesta = (
            "El modelo se valida por clasificación de riesgo, que es lo más fiable para "
            "alerta temprana. En validación cruzada, la banda ALTO concentra ~83% de las "
            "obras con desvío de costo alto real y ~81% en plazo; la banda BAJO, ~14%. "
            "La magnitud exacta (regresión) es orientativa (R² costo ≈ 0.48, tiempo ≈ 0.35). "
            f"Para este proyecto la predicción de costo es {shap['prediccion_pct']}% "
            f"(media histórica {shap['promedio_historico_pct']}%). "
            "Fuente: memoria semántica [[bandas-de-riesgo]] y métricas de validación."
        )
        return _salida(respuesta, trace, intent)

    if intent == 'similares':
        sim = _call('buscar_casos_similares', k=5)
        v = sim['vecinos']
        líneas = '; '.join(
            f"obra {x['id_proyecto']} (desvío costo real {x['desvio_costo_real']}%"
            + (', con episodio' if x['tiene_episodio'] else '') + ')'
            for x in v[:5])
        n_alto = sum(x['desvio_costo_alto'] for x in v)
        respuesta = (
            f"Las {len(v)} obras más comparables: {líneas}. "
            f"De ellas, {n_alto} tuvieron desvío de costo alto real "
            f"(tasa {sim['tasa_desvio_alto_costo']:.0%}). "
            "Es la evidencia empírica que respalda el diagnóstico (capa 4, nearest neighbors)."
        )
        return _salida(respuesta, trace, intent)

    if intent == 'que_bien':
        shap = _call('consultar_shap', target='desvio_costo')
        protect = _fmt_factores(shap['factores'], 'baja', 3)
        ep = _call('buscar_episodio')
        extra = ''
        if ep.get('existe_evidencia') and ep['meta'].get('riesgo_costo') == 'BAJO':
            extra = (f" En la ejecución real, la obra {ep['obra_id']} cerró con un desvío de "
                     f"costo de {ep['meta']['desvio_costo_real']}% (riesgo BAJO): confirma que "
                     "las decisiones estructurales fueron acertadas.")
        respuesta = (
            f"A favor del proyecto (factores que REDUCEN el desvío según SHAP): {protect or '—'}. "
            "Estos son los aspectos estructurales que lo acercan al perfil de bajo desvío."
            + extra + " Fuente: explicabilidad estructural (capa 2)."
        )
        return _salida(respuesta, trace, intent)

    if intent == 'mitigacion':
        shap = _call('consultar_shap', target='desvio_costo')
        causa_preg = _causa_en_pregunta(pregunta)
        if causa_preg:
            # La pregunta nombra una causa concreta: se prioriza esa.
            causa = causa_preg
            fuente = f"la causa que mencionas ({CATEGORIA_NOMBRE.get(causa, causa)})"
        else:
            ep = _call('buscar_episodio')
            if ep.get('existe_evidencia'):
                causa = ep['meta'].get('causa_dominante', 'diseño')
                fuente = f"la causa dominante documentada de esta obra ({CATEGORIA_NOMBRE.get(causa, causa)})"
            else:
                causa = 'diseño'  # causa de mayor peso agregado
                fuente = "las causas de mayor peso en el histórico (diseño y alcance)"
        tag = CAUSA_A_TAG.get(causa, causa)
        mem = _call('leer_memoria', tipo='procedural', tags=[tag])
        pasos = _extraer_pasos(mem)
        respuesta = (
            f"Para mitigar el riesgo, el foco debe estar en {fuente}. "
            f"Procedimiento recomendado:\n{pasos}\n"
            f"Fuente: memoria procedural [[{mem['documentos'][0]['name']}]]." if mem['documentos']
            else f"Para mitigar el riesgo, el foco debe estar en {fuente}."
        )
        return _salida(respuesta, trace, intent)

    # --- diagnóstico (por defecto): estructura + causa, con decisión binaria ---
    shap = _call('consultar_shap', target='desvio_costo')
    sube = _fmt_factores(shap['factores'], 'sube', 3)
    ep = _call('buscar_episodio')

    estructural = (
        f"Estructuralmente, el modelo predice un desvío de costo de {shap['prediccion_pct']}% "
        f"(media histórica {shap['promedio_historico_pct']}%). Los factores que MÁS lo empujan "
        f"al alza son: {sube}. Esta es la causa ex-ante (SHAP, capa 2).")

    if ep.get('existe_evidencia'):
        m = ep['meta']
        causas = m.get('categorias_causa', [])
        dom = CATEGORIA_NOMBRE.get(m.get('causa_dominante'), m.get('causa_dominante'))
        if len(causas) <= 1:
            atrib = f"lo atribuye enteramente a {dom} (causa única documentada)"
        else:
            causas_txt = ', '.join(CATEGORIA_NOMBRE.get(c, c) for c in causas)
            atrib = f"lo atribuye a: {causas_txt}, con {dom} como causa dominante"
        causal = (
            f"En la EJECUCIÓN real, esta obra (id {ep['obra_id']}) tuvo un desvío de costo de "
            f"{m.get('desvio_costo_real')}%, y la evidencia forense DIRECTA (órdenes de cambio) "
            f"{atrib}. Fuente: memoria episódica (órdenes de cambio del proyecto).")
    else:
        sim = _call('buscar_casos_similares', k=5)
        con_ep = [v for v in sim['vecinos'] if v['tiene_episodio']]
        n_alto = sum(v['desvio_costo_alto'] for v in sim['vecinos'])
        ref = (f" Entre las comparables con episodio documentado ({', '.join(str(v['id_proyecto']) for v in con_ep)}), "
               "las causas típicas son diseño y alcance." if con_ep else "")
        causal = (
            "NO hay órdenes de cambio documentadas para este proyecto, así que la atribución de "
            "causa es una inferencia ESTADÍSTICA, no evidencia directa: de "
            f"{sim['k']} obras comparables, {n_alto} tuvieron desvío de costo alto real "
            f"(tasa {sim['tasa_desvio_alto_costo']:.0%})." + ref +
            " Fuente: casos similares (capa 4) + patrones agregados (capa 3).")

    return _salida(estructural + "\n\n" + causal, trace, intent)


def _extraer_pasos(mem: dict, n: int = 4) -> str:
    """Extrae los puntos numerados del procedimiento, uniendo líneas envueltas."""
    if not mem['documentos']:
        return '—'
    body = mem['documentos'][0]['contenido']
    items, cur = [], None
    for line in body.splitlines():
        m = re.match(r'^\d+\.\s+(.*)', line)
        if m:
            if cur is not None:
                items.append(cur)
            cur = m.group(1).strip()
        elif cur is not None:
            s = line.strip()
            if not s or s.startswith('#'):
                items.append(cur)
                cur = None
            else:
                cur += ' ' + s
    if cur is not None:
        items.append(cur)

    def _clean(t):
        t = re.sub(r'\*\*(.+?)\*\*', r'\1', t)      # quita negritas markdown
        return re.sub(r'\s+', ' ', t).strip()

    items = [_clean(i) for i in items][:n]
    return '\n'.join(f'  {i+1}. {p}' for i, p in enumerate(items))


def _salida(respuesta: str, trace: list, intent: str) -> dict:
    return {'respuesta': respuesta.strip(), 'trazabilidad': trace,
            'modo': 'mock', 'intent': intent}
