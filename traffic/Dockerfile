# Build context: repository root. Prepared only; Docker validation is pending.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    API_BASE_URL=http://127.0.0.1:8000

WORKDIR /app
COPY traffic/requirements.txt /app/traffic/requirements.txt
RUN pip install --no-cache-dir -r /app/traffic/requirements.txt \
    && groupadd --gid 10001 cuponmania \
    && useradd --uid 10001 --gid 10001 --no-create-home cuponmania
COPY traffic/__init__.py traffic/main.py /app/traffic/
USER 10001:10001
ENTRYPOINT ["python", "-m", "traffic.main"]
