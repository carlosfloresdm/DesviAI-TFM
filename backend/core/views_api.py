"""
Endpoints JSON de DesviAI (Fase PoC — Día 1/2).

  GET  /api/health          estado + resumen de métricas
  GET  /api/metrics         metrics.json completo (métricas de CV del modelo)
  GET  /api/shap-global     ranking SHAP global por target
  POST /api/predict         desvío + banda + IC80% (costo y tiempo)
  POST /api/explain         descomposición SHAP local (costo y tiempo)

Cuerpo POST: el contrato de proyecto (ver PLAN.md §8), JSON.
"""
from __future__ import annotations
import json

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from core.ml import predictor, explainer
from core.ml import contexto as contexto_mod
from core.ml import historico as historico_mod
from core.ml import validacion
from core.ml.features import TARGETS
from core.ml.artifacts_meta import get_metrics
from core import memory
from core import export as export_mod
from core.agent import service as agent_service
from core.agent import asistente as asistente_ctx

# Claves mínimas del contrato de entrada.
CAMPOS_REQUERIDOS = [
    'sup_m2', 'niveles', 'unidades', 'presupuesto_inicial', 'tiempo_inicial',
    'sistema_constructivo', 'nivel_acabado', 'avance_proyecto',
    'proyectos_similares', 'fecha_inicio',
]


def _parse_project(request):
    """Extrae y valida el proyecto del cuerpo JSON. Devuelve (project, error)."""
    try:
        body = json.loads(request.body or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, 'Cuerpo JSON inválido (se espera JSON codificado en UTF-8).'
    project = body.get('project', body)  # admite {"project": {...}} o el dict directo
    faltan = [c for c in CAMPOS_REQUERIDOS if c not in project]
    if faltan:
        return None, f'Faltan campos requeridos: {", ".join(faltan)}'
    # Errores duros: valores no numéricos o ≤ 0 (impiden predecir; evita el crash).
    errs = validacion.errores(project)
    if errs:
        return None, ' '.join(errs)
    return project, None


def _err(msg, status=400):
    return JsonResponse({'ok': False, 'error': msg}, status=status)


@require_http_methods(['GET'])
def health(request):
    m = get_metrics()
    return JsonResponse({
        'ok': True, 'servicio': 'DesviAI API', 'estado': 'online',
        'modelo': 'RandomForest + SHAP', 'n_obras': m.get('n_obras'),
        'targets': TARGETS,
        'memoria': memory.resumen(),
        'resumen_metricas': {
            t: {'R2': m['regresion'][t]['R2'], 'AUC': m['clasificacion'][t]['AUC']}
            for t in TARGETS
        },
    })


@require_http_methods(['GET'])
def metrics(request):
    return JsonResponse({'ok': True, 'metrics': get_metrics()})


@require_http_methods(['GET'])
def shap_global(request):
    return JsonResponse({'ok': True,
                         'shap_global': {t: explainer.shap_global(t) for t in TARGETS}})


@csrf_exempt
@require_http_methods(['POST'])
def predict(request):
    project, err = _parse_project(request)
    if err:
        return _err(err)
    try:
        return JsonResponse({'ok': True,
                             'prediccion': predictor.predecir_proyecto(project),
                             'advertencias': validacion.advertencias(project)})
    except Exception as exc:  # noqa: BLE001
        return _err(f'Error en la predicción: {exc}', status=500)


@csrf_exempt
@require_http_methods(['POST'])
def explain(request):
    project, err = _parse_project(request)
    if err:
        return _err(err)
    body = json.loads(request.body or '{}')
    target = body.get('target')
    targets = [target] if target in TARGETS else TARGETS
    try:
        return JsonResponse({'ok': True,
                             'explicaciones': {t: explainer.explicar_local(project, t) for t in targets}})
    except Exception as exc:  # noqa: BLE001
        return _err(f'Error en la explicación: {exc}', status=500)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def contexto_config(request):
    """Configuración del formulario de contexto de gestión (+ pre-selección).

    GET devuelve los tipos y opciones; POST admite {project} para incluir la
    sugerencia derivada de los datos ya cargados (avance → madurez).
    """
    project = None
    if request.method == 'POST':
        try:
            body = json.loads(request.body or '{}')
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _err('Cuerpo JSON inválido (se espera JSON codificado en UTF-8).')
        project = body.get('project', body) or None
    return JsonResponse({'ok': True, **contexto_mod.config_formulario(project)})


@csrf_exempt
@require_http_methods(['POST'])
def contexto_calcular(request):
    """Índice de riesgo de contexto de gestión (fórmula ancla determinística)."""
    try:
        body = json.loads(request.body or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _err('Cuerpo JSON inválido (se espera JSON codificado en UTF-8).')
    checklist = body.get('checklist')
    if not isinstance(checklist, dict):
        return _err('Se requiere "checklist" (dict tipo → opción elegida).')
    errores = contexto_mod.validar_checklist(checklist)
    if errores:
        return _err('Checklist inválido: ' + ' · '.join(errores))
    return JsonResponse({'ok': True, 'contexto': contexto_mod.calcular_indice(checklist)})


@csrf_exempt
@require_http_methods(['POST'])
def contexto_explicar(request):
    """Capa interpretativa: explica en lenguaje natural un índice de contexto de
    gestión ya calculado, apoyándose en la memoria. Modo mock/claude/openai según
    AGENT_MODE. El número no se recalcula."""
    try:
        body = json.loads(request.body or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _err('Cuerpo JSON inválido (se espera JSON codificado en UTF-8).')
    resultado = body.get('contexto')
    if not isinstance(resultado, dict) or 'desglose' not in resultado:
        return _err('Se requiere "contexto" (el resultado de /api/contexto/calcular).')
    try:
        return JsonResponse({'ok': True, **asistente_ctx.explicar_riesgo(resultado)})
    except Exception as exc:  # noqa: BLE001
        return _err(f'Error explicando el riesgo: {exc}', status=500)


@require_http_methods(['GET'])
def historico(request):
    """Cartera histórica real (200 obras) con banda de riesgo y flag de episodio."""
    return JsonResponse({'ok': True, **historico_mod.historico()})


@require_http_methods(['GET'])
def atribucion(request):
    """Tabla de atribución agregada por categoría de causa (capa 3, estudio piloto)."""
    path = memory.KNOWLEDGE / 'atribucion_agregada.json'
    if not path.exists():
        return _err('No hay atribución agregada. Ejecuta gen_memoria.py.', status=404)
    return JsonResponse({'ok': True, 'atribucion': json.loads(path.read_text(encoding='utf-8'))})


@require_http_methods(['GET'])
def episodio(request, obra_id):
    """Devuelve el episodio (memoria episódica) de una obra, si existe."""
    doc = memory.get_episodio(int(obra_id))
    if not doc:
        return JsonResponse({'ok': True, 'existe_evidencia': False, 'obra_id': int(obra_id)})
    return JsonResponse({'ok': True, 'existe_evidencia': True,
                         'obra_id': int(obra_id), 'meta': doc['meta'],
                         'contenido': doc['body'], 'path': doc['path']})


def _datos_reporte(request):
    """Parsea el cuerpo y recalcula lo necesario para exportar el reporte.

    Devuelve (datos, error). `datos` = (project, pred, exp, contexto, episodio).
    El contexto de gestión llega ya calculado desde el frontend (es determinístico);
    la predicción y el SHAP se recalculan aquí para que el archivo sea autoritativo.
    """
    project, err = _parse_project(request)
    if err:
        return None, err
    body = json.loads(request.body or '{}')
    contexto = body.get('contexto') if isinstance(body.get('contexto'), dict) else None
    obra_id = body.get('obra_id')
    pred = predictor.predecir_proyecto(project)
    exp = {t: explainer.explicar_local(project, t) for t in TARGETS}
    episodio = memory.get_episodio(int(obra_id)) if obra_id is not None else None
    if episodio:
        episodio = {'obra_id': int(obra_id), 'meta': episodio['meta']}
    return (project, pred, exp, contexto, episodio), None


@csrf_exempt
@require_http_methods(['POST'])
def export_excel(request):
    """Genera y descarga el reporte en Excel (.xlsx)."""
    datos, err = _datos_reporte(request)
    if err:
        return _err(err)
    try:
        contenido = export_mod.build_excel(*datos)
    except Exception as exc:  # noqa: BLE001
        return _err(f'Error generando el Excel: {exc}', status=500)
    resp = HttpResponse(contenido,
                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename="desviai_reporte.xlsx"'
    return resp


@csrf_exempt
@require_http_methods(['POST'])
def export_pdf(request):
    """Genera y descarga el reporte en PDF."""
    datos, err = _datos_reporte(request)
    if err:
        return _err(err)
    try:
        contenido = export_mod.build_pdf(*datos)
    except Exception as exc:  # noqa: BLE001
        return _err(f'Error generando el PDF: {exc}', status=500)
    resp = HttpResponse(contenido, content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="desviai_reporte.pdf"'
    return resp


@csrf_exempt
@require_http_methods(['POST'])
def agent_chat(request):
    """Agente conversacional (capa 6). Modo mock o claude según AGENT_MODE."""
    try:
        body = json.loads(request.body or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _err('Cuerpo JSON inválido (se espera JSON codificado en UTF-8).')
    project = body.get('project')
    pregunta = body.get('pregunta') or body.get('question')
    if not project or not pregunta:
        return _err('Se requieren "project" y "pregunta".')
    faltan = [c for c in CAMPOS_REQUERIDOS if c not in project]
    if faltan:
        return _err(f'Faltan campos del proyecto: {", ".join(faltan)}')
    errs = validacion.errores(project)
    if errs:
        return _err(' '.join(errs))
    try:
        resultado = agent_service.run_agent(
            project, obra_id=body.get('obra_id'),
            pregunta=pregunta, historial=body.get('historial'))
        return JsonResponse({'ok': True, **resultado})
    except Exception as exc:  # noqa: BLE001
        return _err(f'Error del agente: {exc}', status=500)
