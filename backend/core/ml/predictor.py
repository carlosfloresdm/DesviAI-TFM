"""
predictor.py — Predicción de desvío + banda de riesgo + intervalo de confianza.

Carga los artefactos entrenados una sola vez (lazy singleton) y expone
`predecir_proyecto(project)`, que replica la salida del notebook (celda 16)
añadiendo el IC80% real calculado a partir de la dispersión de los árboles del
Random Forest.
"""
from __future__ import annotations
import sys, json, functools
from pathlib import Path

import numpy as np
import joblib

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from features import TARGETS, engineer_one  # noqa: E402

ART = BASE / 'artifacts'
EMOJI_RIESGO = {'BAJO': '🟢', 'MEDIO': '🟡', 'ALTO': '🔴'}


@functools.lru_cache(maxsize=1)
def _load():
    """Carga y cachea todos los artefactos del modelo."""
    meta = json.loads((ART / 'meta.json').read_text(encoding='utf-8'))
    reg = {t: joblib.load(ART / f'reg_{t}.pkl') for t in TARGETS}
    clf = {t: joblib.load(ART / f'clf_{t}.pkl') for t in TARGETS}
    return {'meta': meta, 'reg': reg, 'clf': clf,
            'cortes': tuple(meta['cortes_riesgo'])}


def banda_riesgo(prob: float, cortes=None) -> str:
    lo, hi = cortes or _load()['cortes']
    if prob < lo:
        return 'BAJO'
    if prob < hi:
        return 'MEDIO'
    return 'ALTO'


def _intervalo_arboles(reg_pipeline, X_row, lo=10, hi=90):
    """
    IC calculado con la dispersión de los árboles del Random Forest.
    Cada árbol es una predicción; tomamos percentiles lo/hi (por defecto 80%).
    Devuelve (p_low, p_high, preds_media).
    """
    imp = reg_pipeline.named_steps['imp']
    rf = reg_pipeline.named_steps['m']
    X_imp = imp.transform(X_row)
    tree_preds = np.array([t.predict(X_imp)[0] for t in rf.estimators_])
    return float(np.percentile(tree_preds, lo)), float(np.percentile(tree_preds, hi)), float(tree_preds.mean())


def predecir_proyecto(project: dict) -> dict:
    """
    Para una obra nueva devuelve, en costo y tiempo:
      - desvío estimado (%), banda de riesgo, probabilidad de desvío alto,
      - IC80% del desvío, y el valor final estimado (presupuesto / plazo).
    """
    art = _load()
    X = engineer_one(project)

    out = {}
    for dim, t, final_key, base_val, unidad in [
        ('costo', 'desvio_costo', 'presupuesto_final_est', project['presupuesto_inicial'], None),
        ('tiempo', 'desvio_tiempo', 'tiempo_final_est_dias', project['tiempo_inicial'], 'días'),
    ]:
        desvio = float(art['reg'][t].predict(X)[0])
        prob = float(art['clf'][t].predict_proba(X)[0, 1])
        banda = banda_riesgo(prob, art['cortes'])
        ci_low, ci_high, _ = _intervalo_arboles(art['reg'][t], X)
        final_est = round(base_val * (1 + desvio / 100))
        out[dim] = {
            'riesgo': banda,
            'emoji': EMOJI_RIESGO[banda],
            'probabilidad_alto': round(prob, 3),
            'desvio_estimado_pct': round(desvio, 2),
            'ic80_pct': [round(ci_low, 2), round(ci_high, 2)],
            final_key: final_est,
        }
    return out


if __name__ == '__main__':
    demo = {
        'sup_m2': 45000, 'niveles': 35, 'unidades': 400,
        'presupuesto_inicial': 30_000_000, 'tiempo_inicial': 730,
        'sistema_constructivo': 'Concreto Postensado', 'nivel_acabado': 'Medio',
        'avance_proyecto': '70 - 80', 'proyectos_similares': '10 - 15', 'fecha_inicio': '2024-03',
    }
    print(json.dumps(predecir_proyecto(demo), ensure_ascii=False, indent=2))
