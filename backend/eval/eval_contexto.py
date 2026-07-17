"""
eval_contexto.py — Valida la fórmula del análisis de contexto de gestión.

Corre 5 casos canónicos contra core.ml.contexto.calcular_indice y verifica que la
banda obtenida coincida con la esperada. Es la "métrica" del índice: si todos
pasan, la fórmula ancla está validada. (Diseño y casos del equipo, plataforma
"predictor_obras"; se expresan con opciones concretas del checklist, no con
niveles abstractos.)

Esto valida la parte DETERMINÍSTICA. La capa interpretativa (el LLM que narre el
índice leyendo la memoria) se evaluará aparte, cuando se integre.

Uso:  python eval/eval_contexto.py     (desde backend/)
"""
from __future__ import annotations
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from core.ml import contexto  # noqa: E402

CASOS = [
    {
        'nombre': '1 · Obra ideal',
        'prueba': 'el piso (todo favorable → BAJO)',
        'checklist': {
            'madurez_ejecutivo': 'completo',
            'morfologia': 'regular_repetitivo',
            'geotecnico': 'estudio_completo',
            'regulatorio': 'todo_obtenido',
            'normativas': 'sin_exigencias',
            'contractual': 'intermedio',
            'equipo_decisiones': 'agil',
        },
        'banda_esperada': 'BAJO',
    },
    {
        'nombre': '2 · Tipo dominante',
        'prueba': 'dilución por promedio (un solo Alto aislado)',
        'checklist': {
            'madurez_ejecutivo': 'completo',
            'morfologia': 'regular_repetitivo',
            'geotecnico': 'estudio_completo',
            'regulatorio': 'sin_iniciar',      # el único en el peor valor
            'normativas': 'sin_exigencias',
            'contractual': 'sano',
            'equipo_decisiones': 'normal',
        },
        'banda_esperada': 'BAJO',  # punto de discusión con el profesor
    },
    {
        'nombre': '3 · Riesgo base alto',
        'prueba': 'riesgo estructural puro (amplificador neutro)',
        'checklist': {
            'madurez_ejecutivo': 'preliminar',
            'morfologia': 'alguna_complejidad',
            'geotecnico': 'sin_estudio',
            'regulatorio': 'sin_iniciar',
            'normativas': 'exigente_con_experiencia',
            'contractual': 'tensionado',
            'equipo_decisiones': 'normal',
        },
        'banda_esperada': 'ALTO',
    },
    {
        'nombre': '4 · Amplificador',
        'prueba': 'que el tipo 8 empuje hacia arriba sin cambiar la base',
        'checklist': {
            'madurez_ejecutivo': 'avanzado',
            'morfologia': 'alguna_complejidad',
            'geotecnico': 'estudio_parcial',
            'regulatorio': 'en_tramite',
            'normativas': 'exigente_con_experiencia',
            'contractual': 'intermedio',
            'equipo_decisiones': 'lento_moroso',   # amplificador al máximo
        },
        'banda_esperada': 'MEDIO',  # base media, amplificada al borde de ALTO
    },
    {
        'nombre': '5 · Tormenta perfecta',
        'prueba': 'el techo (todo en contra → ALTO)',
        'checklist': {
            'madurez_ejecutivo': 'preliminar',
            'morfologia': 'compleja_mixta',
            'geotecnico': 'sin_estudio',
            'regulatorio': 'sin_iniciar',
            'normativas': 'exigente_sin_experiencia',
            'contractual': 'tensionado',
            'equipo_decisiones': 'lento_moroso',
        },
        'banda_esperada': 'ALTO',
    },
]


def main() -> int:
    ancho = 84
    print('=' * ancho)
    print('VALIDACIÓN DEL ANÁLISIS DE CONTEXTO DE GESTIÓN — 5 casos canónicos')
    print('=' * ancho)
    print(f'{"Caso":<24}{"base":>7}{"factor":>8}{"índice":>8}{"esper.":>8}{"obten.":>8}   ok')
    print('-' * ancho)

    todos_ok = True
    for c in CASOS:
        r = contexto.calcular_indice(c['checklist'])
        ok = r['banda'] == c['banda_esperada']
        todos_ok = todos_ok and ok
        marca = 'PASA' if ok else 'FALLA <<<'
        print(
            f'{c["nombre"]:<24}'
            f'{r["riesgo_base"]:>7}'
            f'{r["factor_amplificador"]:>8}'
            f'{r["indice"]:>8}'
            f'{c["banda_esperada"]:>8}'
            f'{r["banda"]:>8}   {marca}'
        )

    print('=' * ancho)
    if todos_ok:
        print('RESULTADO: los 5 casos PASAN. La fórmula ancla está validada.')
        return 0
    print('RESULTADO: hay casos que FALLAN. Revisar la fórmula, los pesos o los cortes.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
