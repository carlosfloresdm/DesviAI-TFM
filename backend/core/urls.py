from django.urls import path
from core import views_api as v

urlpatterns = [
    path('health', v.health),
    path('metrics', v.metrics),
    path('shap-global', v.shap_global),
    path('predict', v.predict),
    path('explain', v.explain),
    path('similares', v.similares_view),
    path('score-contextual', v.score_contextual),
    path('historico', v.historico),
    path('atribucion', v.atribucion),
    path('episodio/<int:obra_id>', v.episodio),
    path('agent/chat', v.agent_chat),
]
