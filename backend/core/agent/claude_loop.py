"""
claude_loop.py — Agente real con tool calling de Anthropic (capa 6).

Mismo contrato de salida que el modo mock. Permanece inactivo hasta que exista
ANTHROPIC_API_KEY; se activa con AGENT_MODE=claude. Usa las MISMAS herramientas y el
mismo prompt de sistema (con la regla de decisión binaria).
"""
from __future__ import annotations
import json

from core.agent import tools as T

MAX_ITER = 6


def _context_block(ctx: T.AgentContext) -> str:
    p = ctx.project
    ident = f"obra histórica id {ctx.obra_id}" if ctx.obra_id is not None else "proyecto nuevo (sin id histórico)"
    return (
        f"Proyecto en contexto ({ident}):\n"
        f"- {p.get('sup_m2')} m², {p.get('niveles')} niveles, {p.get('unidades')} unidades\n"
        f"- sistema: {p.get('sistema_constructivo')}, acabado: {p.get('nivel_acabado')}\n"
        f"- presupuesto inicial: {p.get('presupuesto_inicial')} USD, plazo: {p.get('tiempo_inicial')} días\n"
        f"- avance: {p.get('avance_proyecto')}, proyectos similares: {p.get('proyectos_similares')}\n"
        "Usa las herramientas para respaldar cada afirmación."
    )


def run_claude(ctx: T.AgentContext, pregunta: str, historial=None, model: str = 'claude-sonnet-5') -> dict:
    import anthropic
    from django.conf import settings

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    model = getattr(settings, 'AGENT_MODEL', model)

    messages = list(historial or [])
    messages.append({'role': 'user',
                     'content': f"{_context_block(ctx)}\n\nPregunta: {pregunta}"})

    trace = []
    for _ in range(MAX_ITER):
        resp = client.messages.create(
            model=model, max_tokens=1500,
            system=T.SYSTEM_PROMPT, tools=T.TOOLS_SCHEMA, messages=messages,
        )
        if resp.stop_reason != 'tool_use':
            texto = ''.join(b.text for b in resp.content if b.type == 'text')
            return {'respuesta': texto, 'trazabilidad': trace, 'modo': 'claude', 'model': model}

        messages.append({'role': 'assistant', 'content': resp.content})
        results = []
        for b in resp.content:
            if b.type == 'tool_use':
                out = T.TOOLS[b.name](ctx, **b.input)
                trace.append({'paso': len(trace) + 1, 'tool': b.name, 'input': b.input,
                              'resumen': T.resumen_tool(b.name, out)})
                results.append({'type': 'tool_result', 'tool_use_id': b.id,
                                'content': json.dumps(out, ensure_ascii=False, default=str)})
        messages.append({'role': 'user', 'content': results})

    return {'respuesta': 'No se alcanzó una respuesta final (límite de iteraciones).',
            'trazabilidad': trace, 'modo': 'claude', 'model': model}
