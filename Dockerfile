# Imagen de producción de NormaCita (una sola etapa, ligera).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Usuario sin privilegios: si alguien compromete la app, no es root en el contenedor.
RUN useradd --create-home --uid 10001 appuser

COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data
RUN pip install --upgrade pip && pip install .

USER appuser
EXPOSE 8000

# Render/Fly/Railway inyectan PORT; por defecto 8000.
CMD ["sh", "-c", "uvicorn normacita.main:app --host 0.0.0.0 --port ${PORT}"]
