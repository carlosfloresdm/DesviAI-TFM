"""
asistente.py — Capa interpretativa del riesgo de contexto de gestión (Opción B).

Toma un índice de contexto de gestión YA CALCULADO (core.ml.contexto.calcular_indice)
y lo explica en lenguaje natural apoyándose en la memoria (conceptos semánticos +
prácticas procedurales de los factores que salieron riesgosos), SIN recalcular ni
modificar el número. La fórmula ancla (Opción A) sigue siendo la fuente de verdad;
esto sólo la narra.

Idea aportada por el equipo (plataforma predictor_obras, core/asistente.py); aquí
adaptada a nuestra memoria (core.memory, esquema OKF) y a nuestros proveedores
nativos (core.agent.llm), sin langchain. Enruta por AGENT_MODE: en modo simulado
devuelve una plantilla determinística (la demo funciona sin API key); con un LLM
real (claude/openai) genera la explicación apoyada en la memoria.
"""
from __future__ import annotations

from core import memory
from core.ml import contexto as ctx_mod
from core.agent import llm

_SYSTEM = (
    "Eres un asistente experto en riesgo de obras de construcción (AECO). Tu tarea es "
    "explicarle a un profesional, en lenguaje claro y directo, por qué su obra tiene el "
    "nivel de riesgo de GESTIÓN calculado, y qué puede hacer para mitigarlo.\n\n"
    "REGLAS:\n"
    "- Apóyate SOLO en el contexto y la memoria que se te provee. Si algo no está, no lo "
    "inventes.\n"
    "- El número del índice ya está calculado por una fórmula determinística: NO lo "
    "recalcules ni lo cuestiones; explícalo.\n"
    "- Habla en términos CUALITATIVOS ('este factor tiende a generar retrasos'), no "
    "inventes porcentajes de atribución.\n"
    "- Sé concreto y accionable: qué vigilar y qué hacer. Breve: 2-3 párrafos."
)


def _factores_riesgosos(resultado: dict) -> list:
    """Claves de los factores que salieron MEDIO o ALTO (los que importa explicar)."""
    return [clave for clave, d in resultado.get('desglose', {}).items()
            if d.get('nivel') in ('MEDIO', 'ALTO')]


def _memoria_para_riesgo(resultado: dict):
    """Reúne las notas de memoria pertinentes a los factores riesgosos.

    Para cada factor MEDIO/ALTO trae su nota semántica (concepto) y, vía los wikilinks
    de esa nota, las procedurales de mitigación relacionadas. Devuelve
    (texto_para_el_llm, lista_de_fuentes) usando la memoria real (core.memory)."""
    partes, fuentes, vistos = [], [], set()

    def _add(doc):
        if doc and doc['name'] not in vistos:
            vistos.add(doc['name'])
            titulo = doc['meta'].get('titulo', doc['name'])
            partes.append(f"### {titulo} ({doc['memoria']})\n{doc['body'].strip()}")
            fuentes.append({'name': doc['name'], 'titulo': titulo, 'memoria': doc['memoria']})

    for clave in _factores_riesgosos(resultado):
        nota = ctx_mod.TIPOS.get(clave, {}).get('nota_semantica')
        doc = memory.get_doc(nota) if nota else None
        _add(doc)
        if doc:
            for link in memory.wikilinks(doc['body']):
                ligado = memory.get_doc(link)
                if ligado and ligado['memoria'] == 'procedural':
                    _add(ligado)

    return ('\n\n'.join(partes) or '(Sin memoria específica para este perfil.)', fuentes)


def _resumen_riesgo(resultado: dict) -> str:
    lineas = [
        f"Riesgo de gestión: {resultado['banda']} (índice {resultado['indice']} sobre 2).",
        f"Riesgo base: {resultado['riesgo_base']}; factor del equipo (amplificador): "
        f"{resultado['factor_amplificador']}.",
        "Nivel por factor:",
    ]
    for clave, d in resultado['desglose'].items():
        etiqueta = d.get('etiqueta', ctx_mod.TIPOS.get(clave, {}).get('etiqueta', clave))
        lineas.append(f"- {etiqueta}: {d['nivel']} — \"{d['opcion_texto']}\"")
    return '\n'.join(lineas)


def _mock_explicacion(resultado: dict, fuentes: list) -> str:
    """Plantilla determinística (modo simulado): útil, citable, sin API key."""
    riesgosos = _factores_riesgosos(resultado)
    desg = resultado['desglose']
    if riesgosos:
        factores_txt = '; '.join(
            f"{desg[c].get('etiqueta', c)} ({desg[c]['nivel'].lower()}: "
            f"\"{desg[c]['opcion_texto']}\")" for c in riesgosos)
        cuerpo = (
            f"El riesgo de gestión es {resultado['banda']} "
            f"(índice {resultado['indice']} sobre 2 = base {resultado['riesgo_base']} × "
            f"factor del equipo {resultado['factor_amplificador']}). "
            f"Los factores que más lo empujan son: {factores_txt}."
        )
    else:
        cuerpo = (
            f"El riesgo de gestión es {resultado['banda']} "
            f"(índice {resultado['indice']} sobre 2). Ningún factor individual quedó en "
            f"nivel medio o alto: el contexto de gestión de la obra es favorable."
        )
    if fuentes:
        procedurales = [f['titulo'] for f in fuentes if f['memoria'] == 'procedural']
        if procedurales:
            cuerpo += ('\n\nPara mitigarlo, la memoria procedural sugiere revisar: '
                       + '; '.join(procedurales) + '.')
    cuerpo += ('\n\n🔧 (Explicación determinística — sin API key. Con AGENT_MODE=claude '
               'u openai, un LLM redacta esta explicación apoyándose en la misma memoria.)')
    return cuerpo


def explicar_riesgo(resultado: dict) -> dict:
    """Explica un resultado de core.ml.contexto.calcular_indice en lenguaje natural.

    Devuelve {'explicacion', 'modo', 'estado_llm', 'fuentes'}. El número no se toca.
    En modo simulado usa plantilla; con LLM real, lo genera apoyado en la memoria.
    Si el LLM real falla, degrada a la plantilla sin romper la petición.
    """
    memoria_txt, fuentes = _memoria_para_riesgo(resultado)
    modo = llm.modo_llm()

    if modo == 'mock':
        return {'explicacion': _mock_explicacion(resultado, fuentes), 'modo': 'mock',
                'estado_llm': llm.descripcion_estado(), 'fuentes': fuentes}

    contenido = (
        f"Resultado de riesgo a explicar:\n{_resumen_riesgo(resultado)}\n\n"
        f"--- MEMORIA DE APOYO (conceptos y prácticas) ---\n{memoria_txt}\n\n"
        "Explica este riesgo y da recomendaciones, siguiendo tus reglas."
    )
    try:
        texto = llm.completar(_SYSTEM, [{'rol': 'usuario', 'texto': contenido}])
        return {'explicacion': texto, 'modo': modo,
                'estado_llm': llm.descripcion_estado(), 'fuentes': fuentes}
    except Exception as exc:  # noqa: BLE001 — ante error de API, no romper la demo
        r = _mock_explicacion(resultado, fuentes)
        return {'explicacion': r, 'modo': f'mock (fallback por error de API: {exc})',
                'estado_llm': llm.descripcion_estado(), 'fuentes': fuentes}
