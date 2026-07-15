"""
memory.py — Capa de acceso a la base de conocimiento (memorias .md).

Implementa el esquema OKF sugerido por el mentor: archivos Markdown relacionados
por front-matter y wikilinks, organizados en tres memorias:
  - semantica/   conceptos del dominio (QUÉ SABE)
  - procedural/  procedimientos de mitigación (CÓMO SE HACE)
  - episodica/   un episodio por obra cerrada (QUÉ PASÓ)

No hay RAG/vectores: el corpus es pequeño y se recupera por tipo, tags y relaciones.
Los .md son la fuente de verdad; aquí solo se leen y se cachea el índice.
"""
from __future__ import annotations
import functools, re
from pathlib import Path

KNOWLEDGE = Path(__file__).resolve().parents[2] / 'knowledge'


def _coerce(val: str):
    """Convierte un escalar de front-matter a int/float/str."""
    for cast in (int, float):
        try:
            return cast(val)
        except ValueError:
            pass
    return val


def _parse_frontmatter(text: str):
    """Parser mínimo de front-matter YAML (formato controlado por el proyecto)."""
    if not text.startswith('---'):
        return {}, text
    end = text.find('\n---', 3)
    if end == -1:
        return {}, text
    block, body = text[3:end].strip(), text[end + 4:].lstrip('\n')
    meta = {}
    for line in block.splitlines():
        if ':' not in line:
            continue
        key, _, val = line.partition(':')
        key, val = key.strip(), val.strip()
        if val.startswith('[') and val.endswith(']'):
            meta[key] = [x.strip() for x in val[1:-1].split(',') if x.strip()]
        else:
            meta[key] = _coerce(val)
    return meta, body


@functools.lru_cache(maxsize=1)
def _load_all() -> list[dict]:
    """Escanea knowledge/**/*.md y devuelve la lista de documentos parseados."""
    docs = []
    for path in sorted(KNOWLEDGE.rglob('*.md')):
        text = path.read_text(encoding='utf-8')
        meta, body = _parse_frontmatter(text)
        docs.append({
            'name': path.stem,
            'memoria': path.parent.name,          # semantica | procedural | episodica
            'tipo': meta.get('tipo', path.parent.name),
            'meta': meta,
            'body': body,
            'path': str(path.relative_to(KNOWLEDGE)),
        })
    return docs


def reload():
    """Invalida la caché (útil tras regenerar la memoria episódica)."""
    _load_all.cache_clear()


def get_doc(name: str):
    """Devuelve un documento por su nombre (stem), para resolver wikilinks."""
    return next((d for d in _load_all() if d['name'] == name), None)


def list_by(tipo: str = None, tags=None, memoria: str = None) -> list[dict]:
    """Filtra documentos por tipo, memoria y/o tags (cualquier coincidencia)."""
    docs = _load_all()
    if tipo:
        docs = [d for d in docs if d['tipo'] == tipo]
    if memoria:
        docs = [d for d in docs if d['memoria'] == memoria]
    if tags:
        tagset = set(tags)
        docs = [d for d in docs if tagset & set(d['meta'].get('tags', []))]
    return docs


@functools.lru_cache(maxsize=1)
def _episodios_por_obra() -> dict:
    return {int(d['meta']['obra_id']): d
            for d in _load_all() if d['tipo'] == 'episodio' and 'obra_id' in d['meta']}


def obras_con_episodio() -> set:
    """IDs de obra que tienen episodio (memoria episódica / evidencia forense)."""
    return set(_episodios_por_obra().keys())


def get_episodio(obra_id: int):
    """Devuelve el episodio de una obra o None si no hay evidencia directa."""
    return _episodios_por_obra().get(int(obra_id))


def wikilinks(body: str) -> list[str]:
    """Extrae los [[nombres]] enlazados en el cuerpo de un documento."""
    return re.findall(r'\[\[([^\]]+)\]\]', body)


def resumen() -> dict:
    """Conteo por memoria (para health / demo)."""
    docs = _load_all()
    out = {'total': len(docs)}
    for m in ('semantica', 'procedural', 'episodica'):
        out[m] = sum(1 for d in docs if d['memoria'] == m)
    return out
