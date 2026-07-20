"""
openai_loop.py — Agente real con function calling de OpenAI (capa 6).

Alternativa a claude_loop: MISMO contrato de salida, las MISMAS 4 herramientas y el
MISMO prompt de sistema (con la regla de decisión binaria). Se activa con
AGENT_MODE=openai + OPENAI_API_KEY. La única diferencia es de plomería: OpenAI usa
un formato de function calling distinto al de Anthropic, así que aquí se traduce el
esquema de herramientas (`TOOLS_SCHEMA`) al formato de OpenAI y se adapta el bucle.

Usa el SDK nativo `openai` (sin langchain). El import es perezoso para que el
proyecto corra en modo mock/claude aunque `openai` no esté instalado.
"""
from __future__ import annotations
import json

from core.agent import tools as T

MAX_ITER = 6


def _tools_openai() -> list:
    """Traduce TOOLS_SCHEMA (formato Anthropic) al formato de function calling de
    OpenAI. El `input_schema` de Anthropic mapea directo a `parameters`."""
    return [
        {'type': 'function',
         'function': {'name': t['name'],
                      'description': t['description'],
                      'parameters': t['input_schema']}}
        for t in T.TOOLS_SCHEMA
    ]


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


def run_openai(ctx: T.AgentContext, pregunta: str, historial=None, model: str = 'gpt-4o-mini') -> dict:
    from openai import OpenAI
    from django.conf import settings

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    model = getattr(settings, 'OPENAI_MODEL', model)

    # OpenAI lleva el system como primer mensaje de la lista (no en un campo aparte).
    messages = [{'role': 'system', 'content': T.SYSTEM_PROMPT}]
    messages.extend(historial or [])
    messages.append({'role': 'user',
                     'content': f"{_context_block(ctx)}\n\nPregunta: {pregunta}"})

    tools = _tools_openai()
    trace = []
    for _ in range(MAX_ITER):
        resp = client.chat.completions.create(
            model=model, messages=messages, tools=tools, temperature=0,
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            return {'respuesta': msg.content or '', 'trazabilidad': trace,
                    'modo': 'openai', 'model': model}

        # Re-inyecta el turno del asistente (con sus tool_calls) antes de resolverlos.
        messages.append({
            'role': 'assistant',
            'content': msg.content,
            'tool_calls': [
                {'id': tc.id, 'type': 'function',
                 'function': {'name': tc.function.name, 'arguments': tc.function.arguments}}
                for tc in msg.tool_calls
            ],
        })
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or '{}')
            out = T.TOOLS[tc.function.name](ctx, **args)
            trace.append({'paso': len(trace) + 1, 'tool': tc.function.name, 'input': args,
                          'resumen': T.resumen_tool(tc.function.name, out)})
            messages.append({'role': 'tool', 'tool_call_id': tc.id,
                             'content': json.dumps(out, ensure_ascii=False, default=str)})

    return {'respuesta': 'No se alcanzó una respuesta final (límite de iteraciones).',
            'trazabilidad': trace, 'modo': 'openai', 'model': model}
