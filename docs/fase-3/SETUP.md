# Preparación y ejecución local - Fase 3

Esta guía cubre la API simulada y las pruebas locales. Para el stack actual y la API real de preproducción, consultar `docs/elk.md` y `docs/traffic.md`.

## 1. Estructura del repositorio

La raíz contiene `api/`, `traffic/`, `tests/integration/`, `docker-compose.yml`, `elk/`, `evidencias/` y `docs/`. `README.md` y `LICENSE` se conservan. `docs/fase-3/PROMPT_CODEX.md` es el encargo histórico de la primera iteración; las decisiones actuales están en `AGENTS.md` y `docs/sources/aclaraciones-fase-3.md`.

## 2. Python y entorno local (sin Docker)

Desde una terminal en la raíz del repositorio, usa Python 3.13. En esta computadora Windows está disponible Python 3.13.5 y el entorno `.venv`. Para crearlo de nuevo sin alterar Python 3.7 de otro proyecto:

```powershell
& "$env:LOCALAPPDATA/Programs/Python/Python313/python.exe" -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest-tmp-full-local --tb=short
```

En Linux/macOS, si se usa pyenv:

```bash
pyenv shell 3.13.5
python -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q --basetemp=.pytest-tmp-full-local --tb=short
```

En Windows, sustituye `.venv/bin/python` por `.venv/Scripts/python.exe`. No es necesario activar el entorno: los comandos invocan explícitamente `.venv`. Instala dependencias solo dentro de este entorno.

La bitácora registra una ejecución del stack con Docker el 2026-11-10. Docker no es necesario para las pruebas de API y generador descritas aquí.

## 3. Fuente de instrucciones vigente

`AGENTS.md` y `docs/sources/aclaraciones-fase-3.md` recogen la decisión de usar la API real y la ampliación del uso de IA. El prompt antiguo se conserva únicamente para entender la primera iteración. La visualización se realiza en Kibana; no hay frontend propio.

## 4. Ejecutar API, tráfico y pruebas locales

En una terminal PowerShell, desde la raíz:

```powershell
$env:API_LOG_PATH = 'logs/api.log'
$env:API_SEED = '20261103'
.venv/Scripts/python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

En una segunda terminal, desde la misma raíz:

```powershell
# Tráfico finito reproducible en orden de solicitudes; los tiempos son reales.
.venv/Scripts/python.exe -m traffic.main --count 64 --rate 4 --concurrency 1 --mode sequential --seed 20261103
# Tráfico continuo hasta Ctrl+C.
.venv/Scripts/python.exe -m traffic.main --rate 2 --concurrency 2
```

Para obtener una muestra nueva, antes de iniciar la API seleccionar un archivo de evidencia que aún no exista mediante `API_LOG_PATH`, por ejemplo `evidencias/mi-ejecucion-api.log`. La API añade registros; no los sobrescribe. Ejecutar 64 peticiones permite visitar ocho veces cada endpoint. Conservar íntegro el archivo generado: no editar líneas para ajustar porcentajes. El generador imprime su resumen en stdout; el `.log` lo escribe exclusivamente la API.

Pruebas completas: `.venv/bin/python -m pytest -q --basetemp=.pytest-tmp-full-local --tb=short`. El directorio temporal queda en la raíz del proyecto; evita anidarlo dentro de `.pytest_cache`, que pytest puede no haber creado aún. Los tests integrados levantan procesos locales en puertos disponibles y los cierran al terminar. Consultar resultados anteriores y limitaciones en `docs/qa-api-traffic.md`; variables y escenarios en `docs/api.md` y `docs/traffic.md`; payloads y campos en `docs/contracts.md`.

Perfil normal: probabilidades 90% 2xx, 5% 4xx y 5% 5xx; espera simulada uniforme de 80–350 ms. El escenario `--scenario qr-degraded` altera solo emisión y canje QR a 60%/10%/30% y 300–900 ms. Son parámetros de simulación, no resultados medidos ni requisitos literales del profesor. `API_SEED` controla sorteos del servidor; `--seed` controla solicitudes del cliente. No garantizan duraciones idénticas.

## 5. Interfaz de la API simulada

Ambos Dockerfiles se prepararon siguiendo el patrón de imagen oficial y dependencias de la [documentación de FastAPI](https://fastapi.tiangolo.com/deployment/docker/). Su contexto de construcción es la raíz del repositorio; sus ubicaciones son `api/Dockerfile` y `traffic/Dockerfile`. Compose usa el de API para el servicio auxiliar de Heartbeat; el generador principal se ejecuta con Python fuera de los contenedores.

| Programa | Interfaz que conectará el equipo |
| --- | --- |
| API | Puerto interno 8000, escucha 0.0.0.0, un worker; nombre de servicio propuesto `api` |
| Generador | `API_BASE_URL=http://api:8000`; no necesita puerto entrante; por defecto ejecuta continuamente |
| Salud de proceso | GET `/healthz`, estable en 200, separado de los ocho endpoints funcionales |
| Archivo de API | `API_LOG_PATH=/app/logs/api.log`, JSON UTF-8 por línea, append y flush por evento |
| Persistencia | Directorio `/app/logs` escribible para UID/GID 10001 de la API; el equipo dispondrá el volumen compartido de solo lectura para su recolector |
| Rotación | Sin rotación automática; el archivo crece mientras se genera tráfico. El equipo acordará retención/rotación con su recolector; no borrar ni renombrar un archivo abierto sin validar el procedimiento |

El generador tolera fallas de conexión y sigue con la siguiente solicitud, sin reintentos adicionales. API y generador locales no requieren servicios externos ni credenciales. El esquema usa claves JSON planas con puntos. No confundir nanosegundos de `event.duration` con milisegundos, ni `/healthz` con éxito de negocio. El Compose actual usa `api-simulada` como servicio auxiliar de Heartbeat; el tráfico principal va a preproducción con `--target real`.

## 6. Stack actual y revisión

`docker-compose.yml` contiene Elasticsearch, Kibana, Filebeat, Heartbeat y la API simulada auxiliar. Filebeat lee los logs ECS de la API real desde CloudWatch; el generador se ejecuta por separado. `elk/kibana/saved-objects.ndjson` contiene el dashboard y `evidencias/capturas/dashboard-kibana.png` muestra una ejecución real. Los pasos para levantarlo están en `docs/elk.md`.

La ejecución y las pruebas de 2026-11-10 están documentadas en `docs/uso-de-ia.md` y `docs/informe-fase-3.md`. Al repetirlas en otro equipo hay que comprobar el perfil AWS de lectura, permisos, persistencia, ingesta, Heartbeat e importación de Kibana. El informe sigue pendiente de revisión final del equipo. No publicar contraseñas, tokens ni datos personales; usar `.env` local y el perfil AWS temporal.
