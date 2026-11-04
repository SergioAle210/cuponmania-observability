# Contexto de construcción: raíz del repositorio. Pendiente de probar con Docker.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    API_LOG_PATH=/app/logs/api.log
WORKDIR /app

COPY api/requirements.txt /app/api/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/api/requirements.txt \
    && groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid 10001 --no-create-home appuser \
    && mkdir -p /app/logs \
    && chown 10001:10001 /app/logs

COPY api/*.py /app/api/
USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
