# Preparación y ejecución local - Fase 3

Se supone que ya tienes un repositorio `cuponmania-observability` en VS Code. Conserva `README.md` y `LICENSE` originales.

## 1. Incorporar este paquete al repositorio

Extrae el contenido de `cuponmania-phase3-actualizado.zip` **directamente dentro** de la carpeta de tu repositorio. No crees una carpeta anidada `cuponmania-observability/cuponmania-observability/`.

En el explorador de VS Code deberían aparecer `AGENTS.md`, `docs/fase-3/instructions.md`, `docs/fase-3/PROMPT_CODEX.md`, `docs/fase-3/GUIA_FASE3.md`, `docs/`, `assets/brand/`, `.codex/` y las carpetas vacías `api/`, `traffic/`, `tests/integration/` y `logs/`. Los archivos de infraestructura aún no estarán creados: el equipo los elaborará.

## 2. Python y entorno local (sin Docker)

Desde Terminal → New Terminal en VS Code, usando PowerShell en la raíz del repositorio. Esta implementación utiliza Python 3.13. El 3 de noviembre de 2026 se encontró Python 3.13.5 en la ruta siguiente, aunque el comando `python` sin ruta apuntaba a Python 3.7.9 de otro proyecto. No se modificaron el PATH ni otras instalaciones.

```powershell
& 'C:/Users/sergi/AppData/Local/Programs/Python/Python313/python.exe' -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest_cache/full-local --tb=short
```

En otra computadora, sustituir la primera ruta por la de su Python 3.13. No es necesario activar el entorno: los comandos invocan explícitamente `.venv`. Instalar dependencias solo dentro de este entorno. En Linux/macOS usar `python3.13 -m venv .venv` y `.venv/bin/python`.

Docker todavía no está instalado. Los Dockerfiles están preparados y todas las comprobaciones de contenedores permanecen pendientes. No hace falta Docker para estas pruebas locales.

## 3. Iniciar Codex y sus subagentes

Si tienes Codex CLI instalado:

```bash
codex
```

Lee o pega el contenido de `docs/fase-3/PROMPT_CODEX.md`. Si utilizas la extensión de Codex en VS Code, abre el repositorio y copia allí el prompt. Los tres subagentes están definidos en `.codex/agents/`; la configuración limita la concurrencia a tres.

**No instalar ni activar ninguna skill de diseño UI.** Tampoco se requiere React, Next.js, Vite o un frontend.

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

Pruebas completas: `.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest_cache/full-local --tb=short`. El directorio temporal queda dentro del proyecto. Los tests integrados levantan procesos locales en puertos disponibles y los cierran al terminar. Consultar resultados reales y limitaciones en `docs/qa-api-traffic.md`; variables y escenarios en `docs/api.md` y `docs/traffic.md`; payloads y campos en `docs/contracts.md`.

Perfil normal: probabilidades 90% 2xx, 5% 4xx y 5% 5xx; espera simulada uniforme de 80–350 ms. El escenario `--scenario qr-degraded` altera solo emisión y canje QR a 60%/10%/30% y 300–900 ms. Son parámetros de simulación, no resultados medidos ni requisitos literales del profesor. `API_SEED` controla sorteos del servidor; `--seed` controla solicitudes del cliente. No garantizan duraciones idénticas.

## 5. Interfaz para la futura integración del equipo

Ambos Dockerfiles se prepararon siguiendo el patrón de imagen oficial y dependencias de la [documentación de FastAPI](https://fastapi.tiangolo.com/deployment/docker/). Su contexto de construcción es la raíz del repositorio; sus ubicaciones son `api/Dockerfile` y `traffic/Dockerfile`. No se ejecutaron.

| Programa | Interfaz que conectará el equipo |
| --- | --- |
| API | Puerto interno 8000, escucha 0.0.0.0, un worker; nombre de servicio propuesto `api` |
| Generador | `API_BASE_URL=http://api:8000`; no necesita puerto entrante; por defecto ejecuta continuamente |
| Salud de proceso | GET `/healthz`, estable en 200, separado de los ocho endpoints funcionales |
| Archivo de API | `API_LOG_PATH=/app/logs/api.log`, JSON UTF-8 por línea, append y flush por evento |
| Persistencia | Directorio `/app/logs` escribible para UID/GID 10001 de la API; el equipo dispondrá el volumen compartido de solo lectura para su recolector |
| Rotación | Sin rotación automática; el archivo crece mientras se genera tráfico. El equipo acordará retención/rotación con su recolector; no borrar ni renombrar un archivo abierto sin validar el procedimiento |

El equipo comprobará el orden de arranque y la resolución de `api`; el generador tolera fallas de conexión y sigue con la siguiente solicitud, sin reintentos adicionales. API y generador no requieren servicios externos ni credenciales. El esquema usa claves JSON planas con puntos; el equipo debe validar sus tipos en su configuración de ingesta. No confundir nanosegundos de `event.duration` con milisegundos, ni `/healthz` con éxito de negocio.

## 6. Infraestructura y Kibana: trabajo del equipo

Sigue `docs/pasos-kibana-equipo.md` para conocer el orden de configuración y las rutas de la interfaz. El equipo redacta y mantiene `docker-compose.yml`, `filebeat.yml` y `heartbeat.yml` y realiza personalmente las seis visualizaciones.

No incluyas contraseñas, tokens o datos personales en archivos que se publiquen en Git. Utiliza `.env` local (con `.env.example` sin valores secretos si es necesario) y un `.gitignore` apropiado.

## Pendiente: validación con Docker

Todo lo siguiente queda sin ejecutar hasta que el equipo instale Docker y construya su propia configuración:

- [ ] Construir ambas imágenes desde la raíz usando sus Dockerfiles; confirmar instalación de dependencias y usuario no root.
- [ ] Arrancar API y generador en la red que defina el equipo; comprobar resolución de `api:8000` y peticiones a los ocho endpoints.
- [ ] Verificar escritura con UID/GID 10001 sobre el volumen real, lectura del recolector y conservación de logs al reiniciar/recrear la API.
- [ ] Verificar parada por señales y manejo de caída/recuperación entre contenedores, sin procesos huérfanos.
- [ ] Validar ingesta de Filebeat/Logstash y almacenamiento real en Elasticsearch: tipos, siete campos, correspondencia de códigos y ausencia de duplicados.
- [ ] Configurar y comprobar Heartbeat: evidencia real up/down y recuperación.
- [ ] Construir en Kibana las seis visualizaciones (tráfico, tiempo medio, disponibilidad, códigos, error rate, top endpoints), revisar unidades y capturar el dashboard completo.
- [ ] Elaborar interpretación propia, evidencias e informe final con declaración de IA.

Las pruebas locales de API y generador no validan estos puntos ni completan la Fase 3.
