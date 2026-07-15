"""
score.py — Score de riesgo contextual (el mecanismo que pidió el mentor).

Combina, de forma determinística y auditable, tres fuentes de evidencia:

    score = 100 × ( w1·prob_clasificador      (capa 1 — modelo)
                  + w2·tasa_desvio_alto_vecinos (capa 4 — kNN)
                  + w3·señal_episodica )        (memoria episódica)

El LLM NARRA este score; no lo calcula. Cada componente es citable por separado.
"""
from __future__ import annotations
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import predictor  # noqa: E402
import similares as sim  # noqa: E402

# Acceso a la memoria episódica (paquete Django core.memory).
sys.path.insert(0, str(BASE.parent.parent))
from core import memory  # noqa: E402

PESOS = {'w1_modelo': 0.5, 'w2_vecinos': 0.3, 'w3_episodica': 0.2}
CORTES = (0.33, 0.66)


def _banda(frac: float) -> str:
    lo, hi = CORTES
    return 'BAJO' if frac < lo else ('MEDIO' if frac < hi else 'ALTO')


def _senal_episodica(vecinos: list[dict], campo_alto: str):
    """
    Señal de la memoria episódica: entre los vecinos que TIENEN episodio
    documentado, qué fracción terminó con desvío alto real. Si ninguno tiene
    episodio, cae a la tasa de vecinos (evidencia_directa=False).
    """
    con_ep = memory.obras_con_episodio()
    episodicos = [v for v in vecinos if v['id_proyecto'] in con_ep]
    if episodicos:
        frac = sum(v[campo_alto] for v in episodicos) / len(episodicos)
        return frac, True, [v['id_proyecto'] for v in episodicos]
    return None, False, []


def score_contextual(project: dict, k: int = 5, excluir_id=None) -> dict:
    pred = predictor.predecir_proyecto(project)
    similar = sim.buscar_similares(project, k=k, excluir_id=excluir_id)
    vecinos = similar['vecinos']

    out = {'pesos': PESOS, 'k_vecinos': similar['k'], 'dimensiones': {}}

    for dim, campo_alto, tasa_key in [
        ('costo', 'desvio_costo_alto', 'tasa_desvio_alto_costo'),
        ('tiempo', 'desvio_tiempo_alto', 'tasa_desvio_alto_tiempo'),
    ]:
        prob = pred[dim]['probabilidad_alto']
        tasa = similar[tasa_key]
        senal, directa, ids_ep = _senal_episodica(vecinos, campo_alto)
        senal_val = senal if senal is not None else tasa

        frac = (PESOS['w1_modelo'] * prob
                + PESOS['w2_vecinos'] * tasa
                + PESOS['w3_episodica'] * senal_val)
        score = round(frac * 100)
        banda = _banda(frac)

        aporte = {
            'modelo': round(PESOS['w1_modelo'] * prob * 100, 1),
            'vecinos': round(PESOS['w2_vecinos'] * tasa * 100, 1),
            'episodica': round(PESOS['w3_episodica'] * senal_val * 100, 1),
        }

        n_alto = sum(v[campo_alto] for v in vecinos)
        narrativa = (
            f"Score {score}/100 ({banda}). El modelo estima {prob:.0%} de "
            f"probabilidad de desvío alto de {dim}; {n_alto} de {len(vecinos)} obras "
            f"comparables tuvieron desvío alto real"
            + (f"; y de las {len(ids_ep)} con episodio documentado, {senal_val:.0%} "
               f"terminaron desviándose (evidencia directa: obras {', '.join(map(str, ids_ep))})."
               if directa else
               f". No hay obras vecinas con episodio documentado, así que la señal "
               f"episódica usa la tasa de vecinos como estimación (evidencia estadística).")
        )

        out['dimensiones'][dim] = {
            'score': score,
            'banda': banda,
            'componentes': {
                'prob_clasificador': round(prob, 3),
                'tasa_desvio_alto_vecinos': round(tasa, 3),
                'senal_episodica': round(senal_val, 3),
                'evidencia_directa': directa,
                'n_episodios_vecinos': len(ids_ep),
            },
            'aporte_al_score': aporte,
            'narrativa': narrativa,
        }

    return out


if __name__ == '__main__':
    import json
    demo = {
        'sup_m2': 45000, 'niveles': 35, 'unidades': 400,
        'presupuesto_inicial': 30_000_000, 'tiempo_inicial': 730,
        'sistema_constructivo': 'Concreto Postensado', 'nivel_acabado': 'Medio',
        'avance_proyecto': '70 - 80', 'proyectos_similares': '10 - 15', 'fecha_inicio': '2024-03',
    }
    print(json.dumps(score_contextual(demo), ensure_ascii=False, indent=2))
