"""
Ingeniería de variables — fuente única de verdad para entrenamiento y serving.

Reproduce exactamente el feature engineering del notebook
`construccion_predictivo.ipynb` (celdas 5-7). Tanto `train.py` como el predictor
en producción usan estas funciones, de modo que no puede haber desalineación
train/serve (mismas columnas, mismo orden, mismas codificaciones).
"""
from __future__ import annotations
import pandas as pd
import numpy as np

# --- Codificaciones categóricas (idénticas al notebook) ----------------------
AVANCE_ORD = {'60 - 70': 0, '70 - 80': 1, '80 - 90': 2, '90 - 100': 3}
NIVEL_ACABADO_ORD = {'Básico': 0, 'Basico': 0, 'Medio': 1, 'Alto': 2}
# proyectos_similares >= 15 proyectos  ->  experiencia_alta = 1
EXPERIENCIA_ALTA_RANGES = {'15 - 20', '20 +'}
# sistema_constructivo: get_dummies(drop_first=True) descarta 'Concreto Postensado'
# (primero alfabéticamente) y deja una sola columna dummy para 'Concreto Tradicional'.
SISTEMA_COLS = ['sistema_constructivo_Concreto Tradicional']

# Orden EXACTO de las 14 features que consume el modelo. Congelado a propósito.
# Variables EXCLUIDAS a propósito (ver docs/decisiones_variables.md):
#   · Temporales (año/mes/trimestre de inicio): el año causaba extrapolación a
#     fechas futuras y ninguna aportaba señal generalizable (mejoran levemente las
#     4 métricas al quitarlas). La fecha se sigue pidiendo (dato del informe) pero
#     no entra al modelo.
#   · Macroeconómicas: empeoran el modelo en toda configuración probada (al predecir
#     el desvío PORCENTUAL, el efecto macro ya está en el presupuesto base y se cancela).
FEATURES = [
    'sup_m2', 'niveles', 'unidades', 'presupuesto_inicial', 'tiempo_inicial',
    'unidades_por_nivel', 'm2_por_unidad', 'velocidad_obra_m2_dia', 'presupuesto_diario',
    'duracion_meses',
    'avance_ord', 'experiencia_alta', 'nivel_acabado_ord',
] + SISTEMA_COLS

TARGETS = ['desvio_costo', 'desvio_tiempo']

# Columnas prohibidas: contienen información futura (fuga de datos).
PROHIBIDAS = ['costo_m2', 'monto_oc', 'presupuesto_final', 'tiempo_final']


def _add_engineered_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Añade las columnas derivadas comunes (ratios, fechas, ordinales)."""
    df = df.copy()
    # periodo_inicio se conserva para el split temporal (obras antiguas primero),
    # pero año/mes/trimestre YA NO se derivan como features (ver docs/decisiones_variables.md).
    df['periodo_inicio'] = pd.PeriodIndex(pd.to_datetime(df['fecha_inicio']), freq='M')
    df['duracion_meses'] = (df['tiempo_inicial'] / 30.44).round().astype(int)

    df['unidades_por_nivel'] = df['unidades'] / df['niveles']
    df['m2_por_unidad'] = df['sup_m2'] / df['unidades']
    df['velocidad_obra_m2_dia'] = df['sup_m2'] / df['tiempo_inicial']
    df['presupuesto_diario'] = df['presupuesto_inicial'] / df['tiempo_inicial']

    df['avance_ord'] = df['avance_proyecto'].map(AVANCE_ORD)
    return df


def engineer_training(df_raw: pd.DataFrame):
    """
    Prepara el dataset completo para entrenar.

    Devuelve:
      X          -> DataFrame con las 14 features, ORDENADO temporalmente
      y          -> DataFrame con los 2 targets, mismo orden que X
      df_ord     -> dataset completo (features + originales + periodo), mismo orden
    """
    df = _add_engineered_columns(df_raw)

    # experiencia_alta y nivel_acabado_ord ya vienen en el xlsx; se usan tal cual.
    # Preservamos la columna categórica original (get_dummies la consume) para poder
    # mostrarla en casos similares / episodios; NO entra al modelo (no está en FEATURES).
    sistema_orig = df['sistema_constructivo'].copy()
    df = pd.get_dummies(df, columns=['sistema_constructivo'], drop_first=True)
    df['sistema_constructivo'] = sistema_orig
    for col in SISTEMA_COLS:  # robustez si un split no tuviera ambas categorías
        if col not in df.columns:
            df[col] = 0

    # Asserts de seguridad (mismos que el notebook)
    assert len(FEATURES) == len(set(FEATURES)), 'features duplicadas'
    assert not (set(FEATURES) & set(PROHIBIDAS)), 'feature con fuga de datos'
    faltantes = [f for f in FEATURES if f not in df.columns]
    assert not faltantes, f'faltan columnas: {faltantes}'

    # Split temporal: obras antiguas primero.
    orden = df['periodo_inicio'].argsort(kind='stable')
    df_ord = df.iloc[orden].reset_index(drop=True)

    X = df_ord[FEATURES].copy()
    y = df_ord[TARGETS].copy()
    return X, y, df_ord


def engineer_one(project: dict) -> pd.DataFrame:
    """
    Convierte un proyecto nuevo (dict con el contrato de entrada) en una fila X
    alineada a FEATURES. Ver contrato en PLAN.md §8.

    Claves esperadas: sup_m2, niveles, unidades, presupuesto_inicial,
    tiempo_inicial, sistema_constructivo, nivel_acabado, avance_proyecto,
    proyectos_similares, fecha_inicio ('YYYY-MM').
    """
    p = project
    pd.Period(p['fecha_inicio'], freq='M')  # valida el formato de fecha; ya no es feature
    duracion_meses = int(round(p['tiempo_inicial'] / 30.44))

    feats = {
        'sup_m2': p['sup_m2'],
        'niveles': p['niveles'],
        'unidades': p['unidades'],
        'presupuesto_inicial': p['presupuesto_inicial'],
        'tiempo_inicial': p['tiempo_inicial'],
        'unidades_por_nivel': p['unidades'] / p['niveles'],
        'm2_por_unidad': p['sup_m2'] / p['unidades'],
        'velocidad_obra_m2_dia': p['sup_m2'] / p['tiempo_inicial'],
        'presupuesto_diario': p['presupuesto_inicial'] / p['tiempo_inicial'],
        'duracion_meses': duracion_meses,
        'avance_ord': AVANCE_ORD[p['avance_proyecto']],
        'experiencia_alta': 1 if p.get('proyectos_similares') in EXPERIENCIA_ALTA_RANGES else 0,
        'nivel_acabado_ord': NIVEL_ACABADO_ORD.get(p.get('nivel_acabado', 'Medio'), 1),
    }
    for col in SISTEMA_COLS:
        feats[col] = 0
    if p.get('sistema_constructivo') == 'Concreto Tradicional':
        feats['sistema_constructivo_Concreto Tradicional'] = 1

    return pd.DataFrame([feats]).reindex(columns=FEATURES)
