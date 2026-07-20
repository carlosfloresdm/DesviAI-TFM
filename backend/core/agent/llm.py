"""
llm.py — Completado simple del LLM (sin tool calling), agnóstico de proveedor.

Punto único para las llamadas "system + turnos → texto" que NO usan herramientas:
la capa interpretativa del riesgo de gestión (core.agent.asistente) responde de un
tiro, apoyada en un contexto ya armado. El agente con tool calling vive aparte
(claude_loop / openai_loop); esto es para respuestas de un solo paso.

Enruta según AGENT_MODE (mock | claude | openai), la MISMA perilla que el agente,
para no tener dos configuraciones. Usa los SDK nativos (anthropic / openai), sin
langchain; los imports son perezosos para no exigir la librería si no se usa.

Idea del adaptador agnóstico aportada por el equipo (plataforma predictor_obras);
aquí reimplementada con SDK nativos y la config del proyecto, en vez de langchain.
"""
from __future__ import annotations

from django.conf import settings


def modo_llm() -> str:
    """Resuelve el proveedor efectivo AHORA: 'claude', 'openai' o 'mock'.

    Respeta AGENT_MODE, pero degrada a 'mock' si el modo real no tiene su API key
    configurada (misma política de tolerancia que el agente con tools)."""
    modo = getattr(settings, 'AGENT_MODE', 'mock')
    if modo == 'claude' and getattr(settings, 'ANTHROPIC_API_KEY', ''):
        return 'claude'
    if modo == 'openai' and getattr(settings, 'OPENAI_API_KEY', ''):
        return 'openai'
    return 'mock'


def disponible() -> bool:
    """True si hay un LLM real configurado (no modo simulado)."""
    return modo_llm() != 'mock'


def descripcion_estado() -> str:
    """Una línea legible del estado actual, para la interfaz o los logs."""
    modo = modo_llm()
    if modo == 'mock':
        return 'LLM en modo simulado (sin API key). La explicación es determinística.'
    if modo == 'claude':
        return f"LLM real: Claude (Anthropic), modelo {getattr(settings, 'AGENT_MODEL', '?')}."
    return f"LLM real: GPT (OpenAI), modelo {getattr(settings, 'OPENAI_MODEL', '?')}."


def _complete_claude(system: str, turnos: list) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    model = getattr(settings, 'AGENT_MODEL', 'claude-sonnet-5')
    messages = [{'role': 'user' if t['rol'] == 'usuario' else 'assistant',
                 'content': t['texto']} for t in turnos]
    resp = client.messages.create(model=model, max_tokens=1200,
                                  system=system, messages=messages)
    return ''.join(b.text for b in resp.content if b.type == 'text')


def _complete_openai(system: str, turnos: list) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
    messages = [{'role': 'system', 'content': system}] if system else []
    for t in turnos:
        messages.append({'role': 'user' if t['rol'] == 'usuario' else 'assistant',
                         'content': t['texto']})
    resp = client.chat.completions.create(model=model, messages=messages, temperature=0)
    return resp.choices[0].message.content


def completar(system: str, turnos: list) -> str:
    """Genera texto con el proveedor activo. Sólo para modos reales (claude/openai);
    en modo mock lanza RuntimeError (el llamador debe proveer su propia plantilla
    determinística). `turnos`: lista de {'rol': 'usuario'|'asistente', 'texto': str}."""
    modo = modo_llm()
    if modo == 'claude':
        return _complete_claude(system, turnos)
    if modo == 'openai':
        return _complete_openai(system, turnos)
    raise RuntimeError('LLM en modo simulado: no hay proveedor real configurado.')
