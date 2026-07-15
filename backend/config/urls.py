from django.urls import path, include, re_path

from core import views_front as vf

urlpatterns = [
    path('', vf.index),
    path('api/', include('core.urls')),
    # Sirve los assets de la UI (jsx/css/…) desde la raíz del repo, mismo origen.
    re_path(r'^(?P<path>[\w\-./]+\.\w+)$', vf.asset),
]
