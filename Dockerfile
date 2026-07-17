# Imagen para probar DesviAI sin instalar Python ni configurar nada.
# Uso:  docker compose up --build   ->  abrir http://localhost:8200
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 1) Dependencias primero (capa cacheable — no se reinstala si no cambia requirements.txt)
COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

# 2) Código completo del proyecto (backend + knowledge + UI en la raíz del repo)
COPY . .

# 3) Genera los artefactos del modelo y la memoria episódica DENTRO de la imagen
#    (reproducible: no dependemos de archivos generados en la máquina de origen)
WORKDIR /app/backend
RUN python core/ml/train.py && python core/ml/gen_memoria.py

EXPOSE 8200
# Escucha el puerto que asigne el hosting ($PORT) o 8200 en local.
# runserver es suficiente para una demo.
CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:${PORT:-8200} --noreload"]
