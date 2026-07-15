"""
views_front.py — Sirve la UI de DesviAI (React/Babel) desde Django.

Así la interfaz y la API quedan en el MISMO origen (sin CORS). Los archivos viven en
la raíz del repo (un nivel por encima de backend/). Sólo para desarrollo/PoC.
"""
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404

FRONT = settings.BASE_DIR.parent  # raíz del repo (DesviAI.html, *.jsx, styles.css)

_CTYPES = {
    '.html': 'text/html; charset=utf-8',
    '.jsx': 'application/javascript; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.png': 'image/png',
    '.map': 'application/json',
}


def index(request):
    return FileResponse(open(FRONT / 'DesviAI.html', 'rb'),
                        content_type='text/html; charset=utf-8')


def asset(request, path):
    p = (FRONT / path).resolve()
    if FRONT not in p.parents or p.suffix not in _CTYPES or not p.is_file():
        raise Http404('asset no encontrado')
    return FileResponse(open(p, 'rb'), content_type=_CTYPES[p.suffix])
