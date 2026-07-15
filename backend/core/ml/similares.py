"""
similares.py — Casos comparables (capa 4).

kNN sobre las features estandarizadas del histórico. Para una obra consultada
devuelve los k proyectos más parecidos y su desempeño real (desvío final y si
resultó con desvío alto). Es la evidencia empírica que respalda el diagnóstico y
un insumo del score de riesgo contextual.
"""
from __future__ import annotations
import sys, json, functools
from pathlib import Path

import numpy as np
import joblib

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from features import FEATURES, engineer_one  # noqa: E402

ART = BASE / 'artifacts'


@functools.lru_cache(maxsize=1)
def _load():
    knn = joblib.load(ART / 'knn.pkl')
    df = joblib.load(ART / 'dataset_engineered.pkl')
    return {'scaler': knn['scaler'], 'index': knn['index'], 'df': df}


def buscar_similares(project: dict, k: int = 5, excluir_id=None) -> dict:
    """
    Devuelve los k vecinos más cercanos con su desempeño real.
    `excluir_id`: si la obra consultada ya está en el histórico, se excluye a sí
    misma de los resultados.
    """
    art = _load()
    df = art['df']
    X = engineer_one(project)[FEATURES]
    Xs = art['scaler'].transform(X)

    # Pedimos k+1 por si hay que excluir la propia obra.
    dist, idx = art['index'].kneighbors(Xs, n_neighbors=min(k + 1, len(df)))
    dist, idx = dist[0], idx[0]

    vecinos = []
    for d, i in zip(dist, idx):
        row = df.iloc[i]
        if excluir_id is not None and int(row['id_proyecto']) == int(excluir_id):
            continue
        vecinos.append({
            'id_proyecto': int(row['id_proyecto']),
            'similitud': round(float(1 / (1 + d)), 3),  # 1 = idéntico
            'sistema_constructivo': row.get('sistema_constructivo'),
            'nivel_acabado': row.get('nivel_acabado'),
            'sup_m2': int(row['sup_m2']),
            'niveles': int(row['niveles']),
            'desvio_costo_real': round(float(row['desvio_costo']), 2),
            'desvio_tiempo_real': round(float(row['desvio_tiempo']), 2),
            'desvio_costo_alto': int(row['desvio_costo_alto']),
            'desvio_tiempo_alto': int(row['desvio_tiempo_alto']),
        })
        if len(vecinos) >= k:
            break

    # Tasa de desvío alto entre los vecinos (insumo del score contextual).
    tasa_costo = float(np.mean([v['desvio_costo_alto'] for v in vecinos])) if vecinos else 0.0
    tasa_tiempo = float(np.mean([v['desvio_tiempo_alto'] for v in vecinos])) if vecinos else 0.0

    return {'k': len(vecinos), 'vecinos': vecinos,
            'tasa_desvio_alto_costo': round(tasa_costo, 3),
            'tasa_desvio_alto_tiempo': round(tasa_tiempo, 3)}


if __name__ == '__main__':
    demo = {
        'sup_m2': 45000, 'niveles': 35, 'unidades': 400,
        'presupuesto_inicial': 30_000_000, 'tiempo_inicial': 730,
        'sistema_constructivo': 'Concreto Postensado', 'nivel_acabado': 'Medio',
        'avance_proyecto': '70 - 80', 'proyectos_similares': '10 - 15', 'fecha_inicio': '2024-03',
    }
    print(json.dumps(buscar_similares(demo, k=5), ensure_ascii=False, indent=2))
