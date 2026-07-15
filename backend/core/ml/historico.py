"""
historico.py — Resumen de la cartera histórica real (200 obras) para el dashboard
y el historial. Calcula la banda de riesgo de cada obra con el clasificador y anota
si tiene episodio documentado. Cacheado.
"""
from __future__ import annotations
import sys, functools
from pathlib import Path

import joblib

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from features import FEATURES  # noqa: E402
import predictor  # noqa: E402

sys.path.insert(0, str(BASE.parent.parent))
from core import memory  # noqa: E402

ART = BASE / 'artifacts'


@functools.lru_cache(maxsize=1)
def _compute():
    df = joblib.load(ART / 'dataset_engineered.pkl')
    art = predictor._load()
    X = df[FEATURES]
    prob_c = art['clf']['desvio_costo'].predict_proba(X)[:, 1]
    prob_t = art['clf']['desvio_tiempo'].predict_proba(X)[:, 1]
    con_ep = memory.obras_con_episodio()

    obras = []
    for i, (_, r) in enumerate(df.reset_index(drop=True).iterrows()):
        obras.append({
            'id_proyecto': int(r['id_proyecto']),
            'sistema_constructivo': r['sistema_constructivo'],
            'nivel_acabado': r['nivel_acabado'],
            'sup_m2': int(r['sup_m2']), 'niveles': int(r['niveles']), 'unidades': int(r['unidades']),
            'presupuesto_inicial': int(r['presupuesto_inicial']),
            'tiempo_inicial': int(r['tiempo_inicial']),
            'avance_proyecto': r['avance_proyecto'], 'proyectos_similares': r['proyectos_similares'],
            'fecha_inicio': str(r['periodo_inicio']),
            'desvio_costo': round(float(r['desvio_costo']), 2),
            'desvio_tiempo': round(float(r['desvio_tiempo']), 2),
            'prob_costo': round(float(prob_c[i]), 3),
            'prob_tiempo': round(float(prob_t[i]), 3),
            'banda': predictor.banda_riesgo(float(prob_c[i])),
            'tiene_episodio': int(r['id_proyecto']) in con_ep,
        })
    obras.sort(key=lambda o: o['fecha_inicio'], reverse=True)

    dist = {'BAJO': 0, 'MEDIO': 0, 'ALTO': 0}
    for o in obras:
        dist[o['banda']] += 1
    stats = {
        'n_obras': len(obras),
        'distribucion': dist,
        'n_con_episodio': sum(1 for o in obras if o['tiene_episodio']),
        'fecha_min': min(o['fecha_inicio'] for o in obras),
        'fecha_max': max(o['fecha_inicio'] for o in obras),
        'ultima': obras[0]['id_proyecto'] if obras else None,
    }
    return {'stats': stats, 'obras': obras}


def historico():
    return _compute()
