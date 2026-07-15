"""
explainer.py — Explicabilidad SHAP (capa 2).

- `explicar_local(project, target)`: descompone la predicción de una obra en la
  contribución (pts %) de cada variable, ordenada por impacto absoluto, con una
  frase en lenguaje natural (base para el informe).
- `shap_global(target)`: ranking global precalculado en train.py.

El TreeExplainer se construye a partir del RandomForest ya entrenado (no se
reentrena nada); se cachea por target.
"""
from __future__ import annotations
import sys, json, functools
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
import shap

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from features import FEATURES, TARGETS, engineer_one  # noqa: E402

ART = BASE / 'artifacts'

# Nombres legibles para el informe (técnico -> humano)
NOMBRES_LEGIBLES = {
    'sup_m2': 'superficie (m²)', 'niveles': 'número de niveles', 'unidades': 'número de unidades',
    'presupuesto_inicial': 'presupuesto inicial', 'tiempo_inicial': 'plazo inicial',
    'unidades_por_nivel': 'densidad (unidades por nivel)', 'm2_por_unidad': 'm² por unidad',
    'velocidad_obra_m2_dia': 'velocidad de obra (m²/día)', 'presupuesto_diario': 'presupuesto diario',
    'duracion_meses': 'duración (meses)', 'año_inicio': 'año de inicio', 'mes_inicio': 'mes de inicio',
    'trimestre_inicio': 'trimestre de inicio', 'avance_ord': 'nivel de avance del proyecto',
    'experiencia_alta': 'experiencia alta del equipo', 'nivel_acabado_ord': 'nivel de acabado',
    'sistema_constructivo_Concreto Tradicional': 'sistema constructivo',
}


@functools.lru_cache(maxsize=1)
def _load():
    reg = {t: joblib.load(ART / f'reg_{t}.pkl') for t in TARGETS}
    explainers = {t: shap.TreeExplainer(reg[t].named_steps['m']) for t in TARGETS}
    shap_glob = json.loads((ART / 'shap_global.json').read_text(encoding='utf-8'))
    return {'reg': reg, 'explainers': explainers, 'shap_global': shap_glob}


def shap_global(target: str = 'desvio_costo', top_n: int = 12) -> dict:
    art = _load()
    g = art['shap_global'][target]
    return {'target': target, 'base_value': g['base_value'],
            'ranking': g['ranking'][:top_n]}


def explicar_local(project: dict, target: str = 'desvio_costo', top_n: int = 6) -> dict:
    """Descompone la predicción de una obra con TreeSHAP."""
    art = _load()
    reg = art['reg'][target]
    imp = reg.named_steps['imp']
    rf = reg.named_steps['m']

    X = engineer_one(project)
    # El imputer del Pipeline devuelve numpy sin nombres de columna; pasamos numpy
    # a predict/shap (mismo orden que FEATURES) para evitar el warning de sklearn.
    X_imp = imp.transform(X)

    sv = art['explainers'][target].shap_values(X_imp)[0]
    base = art['explainers'][target].expected_value
    base = float(base[0]) if isinstance(base, np.ndarray) else float(base)
    pred = float(rf.predict(X_imp)[0])

    contribs = sorted(
        [{'variable': NOMBRES_LEGIBLES.get(f, f), 'feature': f,
          'contribucion_pts': round(float(s), 2),
          'sentido': 'sube' if s > 0 else 'baja'}
         for f, s in zip(FEATURES, sv)],
        key=lambda d: abs(d['contribucion_pts']), reverse=True)[:top_n]

    p = contribs[0]
    dim = 'costo' if 'costo' in target else 'tiempo'
    resumen = (f"El desvío de {dim} estimado es {pred:.1f}% "
               f"(promedio histórico: {base:.1f}%). El factor de mayor peso es "
               f"'{p['variable']}', que {p['sentido']} el desvío en "
               f"{abs(p['contribucion_pts']):.1f} puntos.")

    return {'target': target, 'prediccion_pct': round(pred, 2),
            'base_pct': round(base, 2), 'contribuciones': contribs,
            'resumen': resumen}


if __name__ == '__main__':
    demo = {
        'sup_m2': 45000, 'niveles': 35, 'unidades': 400,
        'presupuesto_inicial': 30_000_000, 'tiempo_inicial': 730,
        'sistema_constructivo': 'Concreto Postensado', 'nivel_acabado': 'Medio',
        'avance_proyecto': '70 - 80', 'proyectos_similares': '10 - 15', 'fecha_inicio': '2024-03',
    }
    for tgt in TARGETS:
        print(json.dumps(explicar_local(demo, tgt), ensure_ascii=False, indent=2))
