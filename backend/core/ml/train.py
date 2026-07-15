"""
train.py — Reproduce el modelo del notebook y exporta artefactos para servir.

Flujo:
  1. Carga dataset (200 obras) y aplica feature engineering (features.py).
  2. Métricas honestas por validación cruzada (RepeatedKFold para regresión,
     AUC 5-fold para clasificación) -> metrics.json.
  3. Entrena los modelos FINALES sobre las 200 obras (para servir).
  4. SHAP global por target (TreeSHAP) -> shap_global.json.
  5. Índice kNN sobre features estandarizadas (capa 4 / casos similares).
  6. Guarda todos los .pkl + meta.json + dataset_engineered.pkl.

Uso:  python core/ml/train.py     (desde backend/)  ó  python train.py (desde ml/)
"""
from __future__ import annotations
import sys, json
from pathlib import Path

# La consola de Windows usa cp1252 y no puede imprimir caracteres UTF-8 (✅, ±…).
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import numpy as np
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import (RepeatedKFold, KFold, cross_val_score,
                                     cross_val_predict)
from sklearn.metrics import (mean_absolute_error, mean_squared_error, r2_score,
                             roc_auc_score, accuracy_score, f1_score)
import shap

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from features import FEATURES, TARGETS, engineer_training  # noqa: E402

DATA = BASE.parent / 'data' / 'dataset_construccion.xlsx'
ART = BASE / 'artifacts'
ART.mkdir(exist_ok=True)

SEED = 42
np.random.seed(SEED)

# Hiperparámetros afinados por target (idénticos al notebook)
RF_PARAMS = {
    'desvio_costo':  dict(n_estimators=400, max_depth=8,  min_samples_leaf=5,  random_state=SEED),
    'desvio_tiempo': dict(n_estimators=400, max_depth=4,  min_samples_leaf=10, random_state=SEED),
}
CLF_C = {'desvio_costo': 0.5, 'desvio_tiempo': 1.0}  # elegidos por AUC en CV
CORTES_RIESGO = (0.33, 0.66)  # BAJO <0.33 <= MEDIO < 0.66 <= ALTO


def make_reg(target):
    return Pipeline([('imp', SimpleImputer(strategy='median')),
                     ('m',   RandomForestRegressor(**RF_PARAMS[target]))])


def make_clf(target):
    return Pipeline([('imp', SimpleImputer(strategy='median')),
                     ('sc',  StandardScaler()),
                     ('m',   LogisticRegression(C=CLF_C[target], max_iter=1000))])


def main():
    print(f'Cargando dataset: {DATA}')
    df_raw = pd.read_excel(DATA)
    X, y, df_ord = engineer_training(df_raw)
    print(f'  {len(X)} obras x {len(FEATURES)} features')

    metrics = {'n_obras': int(len(X)), 'n_features': len(FEATURES),
               'seed': SEED, 'regresion': {}, 'clasificacion': {}}

    # --- 1. Métricas de REGRESIÓN por CV (RepeatedKFold 5x15) -----------------
    rkf = RepeatedKFold(n_splits=5, n_repeats=15, random_state=SEED)
    print('\n=== Regresión — RepeatedKFold 5x15 ===')
    for t in TARGETS:
        r2 = cross_val_score(make_reg(t), X, y[t], cv=rkf, scoring='r2', n_jobs=-1)
        mae = -cross_val_score(make_reg(t), X, y[t], cv=rkf,
                               scoring='neg_mean_absolute_error', n_jobs=-1)
        base = cross_val_score(DummyRegressor(strategy='mean'), X, y[t], cv=rkf,
                               scoring='r2', n_jobs=-1).mean()
        metrics['regresion'][t] = {'R2': round(float(r2.mean()), 4),
                                   'R2_std': round(float(r2.std()), 4),
                                   'MAE': round(float(mae.mean()), 4),
                                   'baseline_R2': round(float(base), 4)}
        print(f'  {t:15s} R2={r2.mean():+.3f}±{r2.std():.3f}  MAE={mae.mean():.2f}  base={base:+.3f}')

    # --- 2. Métricas de CLASIFICACIÓN por CV (AUC 5-fold) ---------------------
    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
    umbrales, clf_proba_cv = {}, {}
    print('\n=== Clasificación de riesgo (umbral=mediana) — 5-fold ===')
    for t in TARGETS:
        umbrales[t] = float(df_ord[t].median())
        y_bin = (df_ord[t] > umbrales[t]).astype(int).reset_index(drop=True)
        proba = cross_val_predict(make_clf(t), X, y_bin, cv=kf, method='predict_proba')[:, 1]
        clf_proba_cv[t] = proba
        pred = (proba > 0.5).astype(int)
        metrics['clasificacion'][t] = {
            'umbral_mediana': round(umbrales[t], 4),
            'AUC': round(float(roc_auc_score(y_bin, proba)), 4),
            'Acc': round(float(accuracy_score(y_bin, pred)), 4),
            'F1': round(float(f1_score(y_bin, pred)), 4),
            'C': CLF_C[t],
        }
        m = metrics['clasificacion'][t]
        print(f"  {t:15s} AUC={m['AUC']:.3f}  Acc={m['Acc']:.2f}  F1={m['F1']:.2f}")

    # --- 3. Validación de bandas (qué % de cada banda tuvo desvío alto real) --
    def banda(p):
        lo, hi = CORTES_RIESGO
        return 'BAJO' if p < lo else ('MEDIO' if p < hi else 'ALTO')

    metrics['bandas'] = {}
    for t in TARGETS:
        y_bin = (df_ord[t] > umbrales[t]).astype(int).values
        bandas_pred = np.array([banda(p) for p in clf_proba_cv[t]])
        metrics['bandas'][t] = {}
        for b in ['BAJO', 'MEDIO', 'ALTO']:
            mask = bandas_pred == b
            n = int(mask.sum())
            tasa = round(float(y_bin[mask].mean() * 100), 1) if n else None
            metrics['bandas'][t][b] = {'n': n, 'pct_desvio_alto_real': tasa}

    # --- 4. Modelos FINALES sobre las 200 obras (para servir) -----------------
    print('\n=== Entrenando modelos finales sobre las 200 obras ===')
    reg_models, clf_models = {}, {}
    for t in TARGETS:
        reg_models[t] = make_reg(t).fit(X, y[t])
        y_bin = (df_ord[t] > umbrales[t]).astype(int)
        clf_models[t] = make_clf(t).fit(X, y_bin)
        joblib.dump(reg_models[t], ART / f'reg_{t}.pkl')
        joblib.dump(clf_models[t], ART / f'clf_{t}.pkl')
        print(f'  guardado reg_{t}.pkl / clf_{t}.pkl')

    # --- 5. SHAP global por target -------------------------------------------
    print('\n=== SHAP global (TreeSHAP) ===')
    shap_global = {}
    for t in TARGETS:
        rf = reg_models[t].named_steps['m']
        imp = reg_models[t].named_steps['imp']
        X_imp = pd.DataFrame(imp.transform(X), columns=FEATURES, index=X.index)
        explainer = shap.TreeExplainer(rf)
        sv = explainer.shap_values(X_imp)
        base_val = explainer.expected_value
        base_val = float(base_val[0]) if isinstance(base_val, np.ndarray) else float(base_val)
        mean_abs = np.abs(sv).mean(axis=0)
        ranking = sorted(zip(FEATURES, mean_abs), key=lambda x: x[1], reverse=True)
        shap_global[t] = {'base_value': round(base_val, 4),
                          'ranking': [{'feature': f, 'importancia': round(float(v), 4)}
                                      for f, v in ranking]}
        print(f'  {t:15s} top: {ranking[0][0]} ({ranking[0][1]:.3f})')

    # --- 6. Índice kNN (features estandarizadas) -----------------------------
    print('\n=== Índice kNN (casos similares) ===')
    knn_scaler = StandardScaler().fit(X)
    X_scaled = knn_scaler.transform(X)
    knn = NearestNeighbors(n_neighbors=6, metric='euclidean').fit(X_scaled)
    joblib.dump({'scaler': knn_scaler, 'index': knn}, ART / 'knn.pkl')
    print('  guardado knn.pkl')

    # --- 7. Dataset engineered + banda real (para similares/episodios/score) --
    df_out = df_ord.copy()
    df_out['periodo_inicio'] = df_out['periodo_inicio'].astype(str)
    for t in TARGETS:
        df_out[f'{t}_alto'] = (df_out[t] > umbrales[t]).astype(int)
    keep = (['id_proyecto'] + FEATURES + TARGETS +
            ['periodo_inicio', 'fecha_inicio', 'sistema_constructivo',
             'nivel_acabado', 'avance_proyecto', 'proyectos_similares',
             'presupuesto_inicial', 'presupuesto_final', 'tiempo_inicial', 'tiempo_final',
             'desvio_costo_alto', 'desvio_tiempo_alto'])
    keep = [c for c in dict.fromkeys(keep) if c in df_out.columns]
    joblib.dump(df_out[keep], ART / 'dataset_engineered.pkl')
    print(f'  guardado dataset_engineered.pkl ({len(keep)} cols)')

    # --- 8. Metadatos + métricas + SHAP global -------------------------------
    meta = {'features': FEATURES, 'targets': TARGETS, 'umbrales': umbrales,
            'cortes_riesgo': list(CORTES_RIESGO), 'rf_params': RF_PARAMS,
            'clf_C': CLF_C, 'seed': SEED}
    (ART / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    (ART / 'metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8')
    (ART / 'shap_global.json').write_text(json.dumps(shap_global, ensure_ascii=False, indent=2), encoding='utf-8')

    print('\n✅ Artefactos escritos en', ART)
    print('   ', sorted(p.name for p in ART.glob('*')))


if __name__ == '__main__':
    main()
