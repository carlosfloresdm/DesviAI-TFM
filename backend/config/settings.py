"""
Configuración de Django para DesviAI (PoC).

Backend ligero: sirve la API JSON del modelo y (más adelante) la UI estática.
Sin base de datos de negocio — el "estado" vive en los artefactos del modelo y
en la base de conocimiento de archivos .md.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-poc-key-no-usar-en-produccion')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': []},
}]

# SQLite queda configurado por si se necesita, pero el PoC no lo usa.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
# La UI de DesviAI vive en la raíz del repo (un nivel por encima de backend/).
STATICFILES_DIRS = [BASE_DIR.parent]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Configuración del agente ---
# AGENT_MODE elige el proveedor del LLM (Claude y OpenAI son alternativas):
#   'mock'   -> respuestas determinísticas sin LLM (por defecto, gratis, reproducible)
#   'claude' -> Anthropic  (requiere ANTHROPIC_API_KEY; modelo AGENT_MODEL)
#   'openai' -> OpenAI     (requiere OPENAI_API_KEY;    modelo OPENAI_MODEL)
AGENT_MODE = os.getenv('AGENT_MODE', 'mock')  # 'mock' | 'claude' | 'openai'
AGENT_MODEL = os.getenv('AGENT_MODEL', 'claude-sonnet-5')  # si AGENT_MODE=claude
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')     # si AGENT_MODE=openai
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
