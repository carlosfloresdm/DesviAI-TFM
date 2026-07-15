"""
tools.py — Las herramientas del agente (capa 6) y su esquema.

Cada herramienta se apoya en una capa ya construida (SHAP, memoria episódica, kNN,
memorias semántica/procedural). El agente decide vía tool calling cuáles invocar.
La ÚNICA decisión autónoma habilitada es binaria y auditable: si `buscar_episodio`
devuelve evidencia, se prioriza la atribución directa (citando órdenes de cambio);
si no, se recurre a casos similares + inferencia agregada, declarándolo.

Las funciones operan sobre un `AgentContext` (proyecto en discusión + obra_id opcional),
de modo que el modelo no necesita re-enviar los datos del proyecto en cada llamada.
"""
from __future__ import annotations

from core.ml import explainer, similares
from core import memory


class AgentContext:
    """Proyecto sobre el que conversa el agente."""
    def __init__(self, project: dict, obra_id=None):
        self.project = project
        self.obra_id = int(obra_id) if obra_id is not None else None


# --- Implementación de las 4 herramientas ------------------------------------

def consultar_shap(ctx: AgentContext, target: str = 'desvio_costo') -> dict:
    """Capa 2 — explicabilidad estructural del proyecto en contexto."""
    exp = explainer.explicar_local(ctx.project, target=target, top_n=6)
    return {
        'target': target,
        'prediccion_pct': exp['prediccion_pct'],
        'promedio_historico_pct': exp['base_pct'],
        'factores': [
            {'variable': c['variable'], 'contribucion_pts': c['contribucion_pts'],
             'sentido': c['sentido']}
            for c in exp['contribuciones']
        ],
    }


def buscar_episodio(ctx: AgentContext, obra_id=None) -> dict:
    """Capa 3 / memoria episódica — evidencia forense directa, si existe."""
    oid = int(obra_id) if obra_id is not None else ctx.obra_id
    if oid is None:
        return {'existe_evidencia': False,
                'motivo': 'El proyecto en contexto es nuevo (sin id histórico); no hay órdenes de cambio.'}
    doc = memory.get_episodio(oid)
    if not doc:
        return {'existe_evidencia': False, 'obra_id': oid,
                'motivo': 'No hay órdenes de cambio reconstruidas para esta obra.'}
    return {'existe_evidencia': True, 'obra_id': oid,
            'meta': doc['meta'], 'contenido': doc['body']}


def buscar_casos_similares(ctx: AgentContext, k: int = 5) -> dict:
    """Capa 4 — nearest neighbors sobre el histórico, con episodio anotado."""
    r = similares.buscar_similares(ctx.project, k=k, excluir_id=ctx.obra_id)
    con_ep = memory.obras_con_episodio()
    for v in r['vecinos']:
        v['tiene_episodio'] = v['id_proyecto'] in con_ep
    return r


def leer_memoria(ctx: AgentContext, tipo: str = None, tags=None) -> dict:
    """Capa 5 — recuperación sobre la base de conocimiento (semántica/procedural)."""
    if isinstance(tags, str):
        tags = [tags]
    docs = memory.list_by(tipo=tipo, tags=tags)
    docs = [d for d in docs if d['memoria'] in ('semantica', 'procedural')]
    return {'documentos': [
        {'name': d['name'], 'titulo': d['meta'].get('titulo', d['name']),
         'memoria': d['memoria'], 'tags': d['meta'].get('tags', []),
         'contenido': d['body']}
        for d in docs[:4]
    ]}


TOOLS = {
    'consultar_shap': consultar_shap,
    'buscar_episodio': buscar_episodio,
    'buscar_casos_similares': buscar_casos_similares,
    'leer_memoria': leer_memoria,
}


# --- Esquema para el tool calling de Anthropic -------------------------------

TOOLS_SCHEMA = [
    {
        'name': 'consultar_shap',
        'description': ('Devuelve el ranking de variables de diseño que explican el '
                        'riesgo/desvío predicho del proyecto en contexto (SHAP local). '
                        'Úsalo para la causa ESTRUCTURAL (ex-ante).'),
        'input_schema': {
            'type': 'object',
            'properties': {
                'target': {'type': 'string', 'enum': ['desvio_costo', 'desvio_tiempo'],
                           'description': 'Qué desvío explicar. Por defecto costo.'},
            },
        },
    },
    {
        'name': 'buscar_episodio',
        'description': ('Busca las órdenes de cambio reconstruidas de una obra (evidencia '
                        'forense DIRECTA). Devuelve existe_evidencia=false si el proyecto es '
                        'nuevo o no tiene episodio. Úsalo para la causa de EJECUCIÓN (ex-post).'),
        'input_schema': {
            'type': 'object',
            'properties': {
                'obra_id': {'type': 'integer',
                            'description': 'ID de la obra. Omítelo para usar la obra en contexto.'},
            },
        },
    },
    {
        'name': 'buscar_casos_similares',
        'description': ('Devuelve las k obras históricas más comparables y su desempeño real '
                        '(desvío final, si tuvieron desvío alto, si tienen episodio documentado).'),
        'input_schema': {
            'type': 'object',
            'properties': {
                'k': {'type': 'integer', 'description': 'Número de vecinos (por defecto 5).'},
            },
        },
    },
    {
        'name': 'leer_memoria',
        'description': ('Recupera documentos de la base de conocimiento AECO (memoria '
                        'semántica = conceptos; procedural = guías de mitigación). Filtra por '
                        'tipo y/o tags (p.ej. tags=["alcance"] para mitigación de alcance).'),
        'input_schema': {
            'type': 'object',
            'properties': {
                'tipo': {'type': 'string', 'enum': ['semantica', 'procedural'],
                         'description': 'Tipo de memoria a leer.'},
                'tags': {'type': 'array', 'items': {'type': 'string'},
                         'description': 'Tags a filtrar (causas, conceptos).'},
            },
        },
    },
]


SYSTEM_PROMPT = """Eres un experto en gestión de riesgo y costos de proyectos de construcción (AECO).
Respondes, para un proyecto dado, qué explica su riesgo/desvío, qué se hizo bien, qué se
hizo mal y qué se puede aprender. SIEMPRE respaldas tus afirmaciones con las herramientas
disponibles; nunca inventes cifras ni causas.

Regla de decisión (la única autónoma): si `buscar_episodio` devuelve existe_evidencia=true,
prioriza esa evidencia DIRECTA y cita las órdenes de cambio como fuente. Si devuelve
existe_evidencia=false, dilo explícitamente y recurre a `buscar_casos_similares` e inferencia
agregada, dejando claro que es una estimación estadística y no evidencia directa de este
proyecto.

Distingue siempre la causa ESTRUCTURAL (SHAP, ex-ante: por qué el proyecto estaba expuesto)
de la causa de EJECUCIÓN (órdenes de cambio, ex-post: qué ocurrió realmente). Responde en
español, claro y accionable, citando de qué capa proviene cada afirmación."""


def resumen_tool(name: str, output: dict) -> str:
    """Resumen legible de la salida de una tool (para el log de trazabilidad)."""
    if name == 'consultar_shap':
        f = output['factores'][0]
        return (f"{output['target']}: predicción {output['prediccion_pct']}% "
                f"(media {output['promedio_historico_pct']}%); factor top "
                f"'{f['variable']}' {f['contribucion_pts']:+.2f} pts")
    if name == 'buscar_episodio':
        if output.get('existe_evidencia'):
            m = output['meta']
            return (f"evidencia DIRECTA · obra {output['obra_id']} · causa dominante "
                    f"{m.get('causa_dominante')} · desvío real {m.get('desvio_costo_real')}%")
        return f"sin evidencia directa ({output.get('motivo', '')})"
    if name == 'buscar_casos_similares':
        n_ep = sum(1 for v in output['vecinos'] if v.get('tiene_episodio'))
        return (f"{output['k']} vecinos · tasa desvío alto costo "
                f"{output['tasa_desvio_alto_costo']} · {n_ep} con episodio")
    if name == 'leer_memoria':
        nombres = ', '.join(d['name'] for d in output['documentos'])
        return f"{len(output['documentos'])} docs: {nombres}"
    return str(output)[:120]
