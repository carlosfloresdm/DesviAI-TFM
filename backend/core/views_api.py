"""
Endpoints JSON de DesviAI (Fase PoC — Día 1/2).

  GET  /api/health          estado + resumen de métricas
  GET  /api/metrics         metrics.json completo (métricas de CV del modelo)
  GET  /api/shap-global     ranking SHAP global por target
  POST /api/predict         desvío + banda + IC80% (costo y tiempo)
  POST /api/explain         descomposición SHAP local (costo y tiempo)
  POST /api/similares       k proyectos comparables + desempeño real

Cuerpo POST: el contrato de proyecto (ver PLAN.md §8), JSON.
"""
from __future__ import annotations
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from core.ml import predictor, explainer, similares
from core.ml import score as score_mod
from core.ml import historico as historico_mod
from core.ml.features import TARGETS
from core.ml.artifacts_meta import get_metrics
from core import memory
from core.agent import service as agent_service

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
        return JsonResponse({'ok': True, 'prediccion': predictor.predecir_proyecto(project)})
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
@require_http_methods(['POST'])
def similares_view(request):
    project, err = _parse_project(request)
    if err:
        return _err(err)
    body = json.loads(request.body or '{}')
    k = int(body.get('k', 5))
    excluir_id = body.get('excluir_id')
    try:
        return JsonResponse({'ok': True,
                             'similares': similares.buscar_similares(project, k=k, excluir_id=excluir_id)})
    except Exception as exc:  # noqa: BLE001
        return _err(f'Error buscando similares: {exc}', status=500)


@csrf_exempt
@require_http_methods(['POST'])
def score_contextual(request):
    project, err = _parse_project(request)
    if err:
        return _err(err)
    body = json.loads(request.body or '{}')
    k = int(body.get('k', 5))
    excluir_id = body.get('excluir_id')
    try:
        return JsonResponse({'ok': True,
                             'score_contextual': score_mod.score_contextual(project, k=k, excluir_id=excluir_id)})
    except Exception as exc:  # noqa: BLE001
        return _err(f'Error calculando el score: {exc}', status=500)


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
    try:
        resultado = agent_service.run_agent(
            project, obra_id=body.get('obra_id'),
            pregunta=pregunta, historial=body.get('historial'))
        return JsonResponse({'ok': True, **resultado})
    except Exception as exc:  # noqa: BLE001
        return _err(f'Error del agente: {exc}', status=500)
