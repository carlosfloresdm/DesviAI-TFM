"""
contexto.py — Análisis de contexto de gestión (fórmula ancla determinística).

Evalúa el CONTEXTO DE GESTIÓN de una obra mediante un checklist de 8 tipos de
riesgo y produce un índice cualitativo (BAJO / MEDIO / ALTO). Esta lectura CONVIVE
en paralelo con la predicción del modelo ML y con el score de riesgo contextual
(modelo + vecinos + episódica): no los modifica ni los reemplaza. Mide lo que las
dimensiones de diseño no capturan: madurez del ejecutivo, permisos, terreno,
contrato, cliente.

Diseño (aporte del equipo, plataforma "predictor_obras"):
- Cada tipo hace una PREGUNTA CONCRETA con opciones específicas (no niveles
  abstractos BAJO/MEDIO/ALTO): el usuario responde algo que conoce de su obra y
  el sistema traduce la opción a un peso por detrás.
- Cada opción declara un peso NORMALIZADO en [0, 1] (0 = no aporta riesgo,
  1 = peor escenario del tipo). Así un tipo con 4 opciones pesa lo mismo que uno
  con 2: más opciones = más matiz, no más peso relativo.
- Los tipos "base" (1-6) promedian; el tipo 8 ("amplificador") multiplica; el
  tipo 7 ("diferido") queda contemplado pero fuera del cálculo en el PoC.
- Es el ANCLA determinística: mismas respuestas → mismo índice, seguible con
  lápiz. El LLM (capa interpretativa, futura) lo narra; no lo calcula.

Python puro (solo librería estándar). Devuelve datos, no presentación.
"""
from __future__ import annotations

# El riesgo base final se expresa en 0-2 (cortes validados con los 5 casos
# canónicos); el promedio normalizado 0-1 se reescala multiplicando por esto.
ESCALA_BASE = 2.0

# ──────────────────────────────────────────────────────────────────────────────
# LOS 8 TIPOS DE RIESGO CONTEXTUAL
#   rol: "base" promedia · "amplificador" multiplica · "diferido" no calcula aún
#   nota_semantica: archivo de knowledge/semantica/ que explica el tipo
#   deriva_de: campo del contrato del modelo del que se pre-selecciona opción
#   Los pesos son heurísticos (criterio de dominio); viven todos acá para poder
#   ajustarlos sin tocar la fórmula.
# ──────────────────────────────────────────────────────────────────────────────
TIPOS = {
    'madurez_ejecutivo': {
        'etiqueta': 'Madurez del proyecto ejecutivo',
        'pregunta': '¿Qué nivel de definición tiene el proyecto ejecutivo al iniciar la obra?',
        'rol': 'base',
        'nota_semantica': 'contexto-madurez-ejecutivo',
        'deriva_de': 'avance_proyecto',
        'opciones': [
            {'id': 'completo', 'texto': 'Planos, especificaciones y catálogo completos y coordinados (BIM al día)', 'peso': 0.0},
            {'id': 'avanzado', 'texto': 'Mayormente definido, con algunas disciplinas por coordinar', 'peso': 0.4},
            {'id': 'parcial', 'texto': 'Definición parcial, especificaciones genéricas en varias partidas', 'peso': 0.7},
            {'id': 'preliminar', 'texto': 'Se licita sobre anteproyecto / preliminares, a definir en obra', 'peso': 1.0},
        ],
    },
    'morfologia': {
        'etiqueta': 'Morfología y complejidad',
        'pregunta': '¿Cómo es la geometría y el programa del edificio?',
        'rol': 'base',
        'nota_semantica': 'contexto-morfologia-complejidad',
        'opciones': [
            {'id': 'regular_repetitivo', 'texto': 'Forma regular y plantas repetitivas, un solo uso', 'peso': 0.0},
            {'id': 'alguna_complejidad', 'texto': 'Alguna irregularidad o elementos especiales acotados', 'peso': 0.5},
            {'id': 'compleja_mixta', 'texto': 'Forma irregular/orgánica, baja repetitividad o programa mixto', 'peso': 1.0},
        ],
    },
    'geotecnico': {
        'etiqueta': 'Riesgo geotécnico y entorno',
        'pregunta': '¿Qué información del terreno tienes al momento de proyectar la cimentación?',
        'rol': 'base',
        'nota_semantica': 'contexto-riesgo-geotecnico',
        'opciones': [
            {'id': 'estudio_completo', 'texto': 'Estudio de mecánica de suelos completo y terreno homogéneo', 'peso': 0.0},
            {'id': 'estudio_parcial', 'texto': 'Estudio con pocos sondeos, o terreno con cierta variabilidad', 'peso': 0.5},
            {'id': 'referencia_vecina', 'texto': 'Sin estudio propio: se extrapola de un terreno vecino', 'peso': 0.8},
            {'id': 'sin_estudio', 'texto': 'Sin estudio de suelos, o zona de relleno / napa alta conocida', 'peso': 1.0},
        ],
    },
    'regulatorio': {
        'etiqueta': 'Riesgo regulatorio y permisos',
        'pregunta': '¿En qué estado están los permisos y factibilidades al iniciar?',
        'rol': 'base',
        'nota_semantica': 'contexto-riesgo-regulatorio',
        'opciones': [
            {'id': 'todo_obtenido', 'texto': 'Licencia y factibilidades obtenidas antes de movilizar', 'peso': 0.0},
            {'id': 'licencia_ok_falta_factib', 'texto': 'Licencia obtenida, alguna factibilidad pendiente', 'peso': 0.4},
            {'id': 'en_tramite', 'texto': 'Licencia en trámite avanzado al iniciar', 'peso': 0.7},
            {'id': 'sin_iniciar', 'texto': 'Licencia recién iniciada o sin presentar, o municipio de plazos largos', 'peso': 1.0},
        ],
    },
    'normativas': {
        'etiqueta': 'Normativas y certificaciones',
        'pregunta': '¿Hay exigencias de certificación especiales, y qué experiencia tiene el equipo en ellas?',
        'rol': 'base',
        'nota_semantica': 'contexto-normativas-certificaciones',
        'opciones': [
            {'id': 'sin_exigencias', 'texto': 'Sin certificaciones especiales más allá de la normativa estándar', 'peso': 0.0},
            {'id': 'exigente_con_experiencia', 'texto': 'Certificación exigente (LEED u otra), pero el equipo ya la hizo antes', 'peso': 0.4},
            {'id': 'exigente_sin_experiencia', 'texto': 'Certificación exigente y el equipo no tiene experiencia previa en ella', 'peso': 1.0},
        ],
    },
    'contractual': {
        'etiqueta': 'Estructura contractual y financiamiento',
        'pregunta': '¿Cómo es la estructura de pagos y la exposición financiera del contrato?',
        'rol': 'base',
        'nota_semantica': 'contexto-estructura-contractual',
        'opciones': [
            {'id': 'sano', 'texto': 'Anticipo razonable, pagos frecuentes y escalatorias pactadas', 'peso': 0.0},
            {'id': 'intermedio', 'texto': 'Anticipo bajo o pagos mensuales, sin protección inflacionaria', 'peso': 0.5},
            {'id': 'tensionado', 'texto': 'Sin anticipo, pagos espaciados, o exposición cambiaria sin cobertura', 'peso': 1.0},
        ],
    },
    'senales_ejecucion': {
        'etiqueta': 'Señales tempranas en ejecución',
        'pregunta': '(Dinámico — se evaluará durante la ejecución de la obra)',
        'rol': 'diferido',  # requiere bitácora de ejecución; no existe en el PoC
        'nota_semantica': 'contexto-senales-ejecucion',
        'opciones': [],
    },
    'equipo_decisiones': {
        'etiqueta': 'Equipo y flujo de decisiones',
        'pregunta': '¿Cómo funciona la toma de decisiones y el flujo de pagos del lado del cliente?',
        'rol': 'amplificador',
        'nota_semantica': 'contexto-equipo-decisiones',
        'opciones': [
            {'id': 'agil', 'texto': 'Interlocutor único con decisión, aprobaciones ágiles y pagos en fecha', 'peso': 0.0},
            {'id': 'normal', 'texto': 'Cadena de aprobación razonable, sin historial de morosidad', 'peso': 0.5},
            {'id': 'lento_moroso', 'texto': 'Muchos aprobadores, jerarquía larga o historial de pagos atrasados', 'peso': 1.0},
        ],
    },
}

# El amplificador no promedia: su peso [0,1] se convierte en factor multiplicativo.
#   peso 0.0 → 0.8 (equipo ágil, atenúa) · peso 1.0 → 1.3 (lento/moroso, agrava)
FACTOR_MIN = 0.8
FACTOR_MAX = 1.3

# Cortes de banda sobre el índice en escala 0-2.
CORTE_BAJO = 0.66
CORTE_ALTO = 1.33

# Pre-selección desde el contrato del modelo: avance_proyecto → madurez_ejecutivo
# (relación inversa: más avance, menos riesgo de definición pendiente).
_MAPA_AVANCE_A_MADUREZ = {
    '60 - 70': 'preliminar',
    '70 - 80': 'parcial',
    '80 - 90': 'avanzado',
    '90 - 100': 'completo',
}


def tipos_base() -> list:
    """Los tipos que promedian para el riesgo base (rol 'base')."""
    return [k for k, cfg in TIPOS.items() if cfg['rol'] == 'base']


def tipo_amplificador() -> str:
    """La clave del único tipo con rol 'amplificador' (el tipo 8)."""
    for k, cfg in TIPOS.items():
        if cfg['rol'] == 'amplificador':
            return k
    raise RuntimeError("No hay ningún tipo con rol 'amplificador' en TIPOS.")


def tipos_activos() -> list:
    """Tipos que participan del cálculo (base + amplificador); excluye diferidos."""
    return [k for k, cfg in TIPOS.items() if cfg['rol'] in ('base', 'amplificador')]


def opciones_de(clave: str) -> list:
    """Las opciones de un tipo (lista de dicts con id/texto/peso)."""
    return TIPOS[clave]['opciones']


def _ids_validos(clave: str) -> list:
    return [op['id'] for op in TIPOS[clave]['opciones']]


def _peso_de_opcion(clave: str, opcion_id: str) -> float:
    for op in TIPOS[clave]['opciones']:
        if op['id'] == opcion_id:
            return op['peso']
    raise KeyError(f"'{opcion_id}' no es una opción válida de '{clave}'.")


def validar_checklist(checklist: dict) -> list:
    """Devuelve la lista de errores del checklist (vacía si está bien formado).

    No lanza excepción: la interfaz puede mostrar todos los problemas juntos.
    Los tipos diferidos se ignoran si aparecen.
    """
    errores = []
    for k in tipos_activos():
        if k not in checklist:
            errores.append(f"Falta responder: '{k}' ({TIPOS[k]['etiqueta']}).")
    for k, opcion_id in checklist.items():
        if k in TIPOS and TIPOS[k]['rol'] == 'diferido':
            continue
        if k not in TIPOS:
            errores.append(f"'{k}' no es un tipo de riesgo conocido.")
        elif opcion_id not in _ids_validos(k):
            errores.append(
                f"'{k}' tiene una opción inválida: {opcion_id!r}. "
                f"Debe ser una de {_ids_validos(k)}.")
    return errores


def sugerir_desde_obra(project: dict) -> dict:
    """Checklist PARCIAL pre-seleccionado desde campos que el usuario ya cargó.

    El sistema propone, el usuario dispone: la decisión final es del usuario.
    """
    sugerencia = {}
    avance = project.get('avance_proyecto')
    if avance in _MAPA_AVANCE_A_MADUREZ:
        sugerencia['madurez_ejecutivo'] = _MAPA_AVANCE_A_MADUREZ[avance]
    return sugerencia


def _nivel_cualitativo(peso: float) -> str:
    """Etiqueta del semáforo por tipo (solo presentación del desglose)."""
    if peso < 0.34:
        return 'BAJO'
    if peso < 0.67:
        return 'MEDIO'
    return 'ALTO'


def _banda(indice: float) -> str:
    if indice < CORTE_BAJO:
        return 'BAJO'
    if indice >= CORTE_ALTO:
        return 'ALTO'
    return 'MEDIO'


def calcular_indice(checklist: dict) -> dict:
    """Calcula el índice de riesgo de gestión a partir del checklist.

    Fórmula (ancla determinística):
        riesgo_base = promedio(pesos tipos base) × ESCALA_BASE   → [0, 2]
        factor      = FACTOR_MIN + peso_amplificador × (FACTOR_MAX − FACTOR_MIN)
        indice      = riesgo_base × factor
        banda       = BAJO / MEDIO / ALTO según los cortes

    Lanza ValueError si el checklist está incompleto o mal formado.
    """
    errores = validar_checklist(checklist)
    if errores:
        raise ValueError('Checklist inválido:\n- ' + '\n- '.join(errores))

    claves_base = tipos_base()
    pesos_base = [_peso_de_opcion(k, checklist[k]) for k in claves_base]
    riesgo_base = (sum(pesos_base) / len(pesos_base)) * ESCALA_BASE

    clave_amp = tipo_amplificador()
    peso_amp = _peso_de_opcion(clave_amp, checklist[clave_amp])
    factor = FACTOR_MIN + peso_amp * (FACTOR_MAX - FACTOR_MIN)

    indice = riesgo_base * factor

    desglose = {}
    for k in tipos_activos():
        opcion_id = checklist[k]
        peso = _peso_de_opcion(k, opcion_id)
        texto = next(op['texto'] for op in TIPOS[k]['opciones'] if op['id'] == opcion_id)
        desglose[k] = {
            'etiqueta': TIPOS[k]['etiqueta'],
            'opcion_id': opcion_id,
            'opcion_texto': texto,
            'peso': round(peso, 2),
            'nivel': _nivel_cualitativo(peso),
            'rol': TIPOS[k]['rol'],
            'nota_semantica': TIPOS[k]['nota_semantica'],
        }

    return {
        'indice': round(indice, 2),
        'banda': _banda(indice),
        'riesgo_base': round(riesgo_base, 2),
        'factor_amplificador': round(factor, 2),
        'desglose': desglose,
    }


def config_formulario(project: dict | None = None) -> dict:
    """Configuración del formulario para la UI (única fuente de verdad).

    No expone los pesos: el usuario responde preguntas concretas y la mecánica
    queda por detrás (mostrar los pesos volvería el índice una tautología).
    """
    tipos = []
    for k in tipos_activos():
        cfg = TIPOS[k]
        tipos.append({
            'clave': k,
            'etiqueta': cfg['etiqueta'],
            'pregunta': cfg['pregunta'],
            'rol': cfg['rol'],
            'opciones': [{'id': op['id'], 'texto': op['texto']} for op in cfg['opciones']],
        })
    return {'tipos': tipos,
            'sugerencia': sugerir_desde_obra(project) if project else {}}


if __name__ == '__main__':
    import json
    demo = {k: opciones_de(k)[0]['id'] for k in tipos_activos()}
    print(json.dumps(calcular_indice(demo), ensure_ascii=False, indent=2))
