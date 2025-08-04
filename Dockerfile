# Imagen base oficial ligera de Python 3.10
FROM python:3.10-slim

# Evita prompts interactivos y optimiza logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para youtube-transcript-api y google-cloud
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar solo requirements primero (mejora el cache de Docker)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer puerto para Cloud Run (por defecto 8080)
ENV PORT=8080

# Comando para levantar Flask usando gunicorn (más eficiente en Cloud Run)
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 main:app
