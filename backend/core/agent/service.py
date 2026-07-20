"""
service.py — Punto de entrada del agente. Elige modo (mock / claude / openai) según
config. Claude y OpenAI son alternativas intercambiables: mismas herramientas, mismo
prompt, mismo contrato de salida; solo cambia el proveedor del LLM.
"""
from __future__ import annotations

from django.conf import settings

from core.agent import tools as T
from core.agent import mock, claude_loop, openai_loop


def run_agent(project: dict, obra_id=None, pregunta: str = '', historial=None) -> dict:
    ctx = T.AgentContext(project, obra_id)
    modo = getattr(settings, 'AGENT_MODE', 'mock')

    if modo == 'claude':
        if not getattr(settings, 'ANTHROPIC_API_KEY', ''):
            r = mock.run_mock(ctx, pregunta)
            r['modo'] = 'mock (sin ANTHROPIC_API_KEY)'
            return r
        try:
            return claude_loop.run_claude(ctx, pregunta, historial)
        except Exception as exc:  # noqa: BLE001 — ante error de API, no romper la demo
            r = mock.run_mock(ctx, pregunta)
            r['modo'] = f'mock (fallback por error de API: {exc})'
            return r

    if modo == 'openai':
        if not getattr(settings, 'OPENAI_API_KEY', ''):
            r = mock.run_mock(ctx, pregunta)
            r['modo'] = 'mock (sin OPENAI_API_KEY)'
            return r
        try:
            return openai_loop.run_openai(ctx, pregunta, historial)
        except Exception as exc:  # noqa: BLE001 — ante error de API, no romper la demo
            r = mock.run_mock(ctx, pregunta)
            r['modo'] = f'mock (fallback por error de API: {exc})'
            return r

    return mock.run_mock(ctx, pregunta)
