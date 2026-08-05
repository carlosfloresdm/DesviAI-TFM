"""
validacion.py — Coherencia de los campos numéricos de entrada.

Distingue dos niveles, a propósito:

  · ERRORES (bloquean): valores imposibles de procesar o sin sentido físico
    (no numéricos, o ≤ 0 en campos que deben ser positivos). Con estos no se
    puede calcular una predicción —dividir por cero o predecir sobre un
    presupuesto negativo no significa nada—, así que se rechazan con un mensaje
    claro (evita además el crash de división por cero).

  · ADVERTENCIAS (no bloquean): el valor es un número válido pero cae FUERA del
    rango histórico con el que se entrenó el modelo. En ese caso el modelo
    EXTRAPOLA: sigue devolviendo una predicción, pero es menos fiable. No se
    bloquea —el modelo puede extrapolar— pero se avisa.

Los rangos son los del dataset de entrenamiento (200 obras). Python puro.
"""
from __future__ import annotations

# Rango [mín, máx] observado en el histórico, por campo numérico, y su etiqueta.
# Fuera de estos límites el modelo extrapola (predicción menos fiable).
RANGOS = {
    'sup_m2':              {'min': 8_340,     'max': 56_538,     'etiqueta': 'Superficie',        'unidad': 'm²'},
    'niveles':             {'min': 12,        'max': 42,         'etiqueta': 'Número de niveles', 'unidad': 'niveles'},
    'unidades':            {'min': 36,        'max': 612,        'etiqueta': 'Número de unidades','unidad': 'unidades'},
    'presupuesto_inicial': {'min': 3_984_000, 'max': 43_680_000, 'etiqueta': 'Presupuesto inicial','unidad': 'USD'},
    'tiempo_inicial':      {'min': 420,       'max': 990,        'etiqueta': 'Plazo inicial',     'unidad': 'días'},
}

# Campos que deben ser estrictamente positivos (≤ 0 rompe el cálculo de features).
POSITIVOS = list(RANGOS.keys())


def _num(v):
    """Intenta convertir a número; None si no se puede."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _fmt(n) -> str:
    """Formatea un número con separador de miles (para los mensajes)."""
    try:
        return f'{n:,.0f}'.replace(',', '.')
    except (TypeError, ValueError):
        return str(n)


def errores(project: dict) -> list:
    """Errores que impiden predecir (no numérico, o ≤ 0 en campos positivos).

    Devuelve lista de mensajes (vacía si todo bien). No lanza excepción."""
    errs = []
    for campo in POSITIVOS:
        if campo not in project:
            continue  # la presencia la valida el endpoint (CAMPOS_REQUERIDOS)
        n = _num(project[campo])
        etiqueta = RANGOS[campo]['etiqueta']
        if n is None:
            errs.append(f'{etiqueta} debe ser un número.')
        elif n <= 0:
            errs.append(f'{etiqueta} debe ser mayor que 0 (llegó {project[campo]}).')
    return errs


def advertencias(project: dict) -> list:
    """Advertencias por valores fuera del rango histórico (no bloquean).

    Devuelve lista de dicts {campo, mensaje, valor, rango} para que la interfaz
    los muestre. Solo para valores numéricos y > 0 (los inválidos ya son errores)."""
    avisos = []
    for campo, r in RANGOS.items():
        if campo not in project:
            continue
        n = _num(project[campo])
        if n is None or n <= 0:
            continue  # eso es un error, no una advertencia
        if n < r['min'] or n > r['max']:
            avisos.append({
                'campo': campo,
                'valor': project[campo],
                'rango': [r['min'], r['max']],
                'mensaje': (
                    f"{r['etiqueta']} ({_fmt(n)} {r['unidad']}) está fuera del rango "
                    f"histórico ({_fmt(r['min'])}–{_fmt(r['max'])} {r['unidad']}); "
                    f"la estimación es menos fiable."
                ),
            })
    return avisos
