"""Acceso cacheado a los metadatos y métricas de los artefactos."""
from __future__ import annotations
import json, functools
from pathlib import Path

ART = Path(__file__).resolve().parent / 'artifacts'


@functools.lru_cache(maxsize=1)
def get_metrics() -> dict:
    return json.loads((ART / 'metrics.json').read_text(encoding='utf-8'))


@functools.lru_cache(maxsize=1)
def get_meta() -> dict:
    return json.loads((ART / 'meta.json').read_text(encoding='utf-8'))
