# API simulada de CupónManía

Implementación FastAPI sin base de datos ni integraciones externas. Las ocho rutas simulan operaciones del catálogo; no crean tickets Jira ni realizan compras, QR utilizables, cambios de cuentas o reembolsos. El contrato de cuerpos, respuestas y componentes está en [contracts.md](contracts.md).

## Ejecución local sin Docker

Desde la raíz del repositorio, con el entorno `.venv` preparado según [SETUP.md](fase-3/SETUP.md):

```powershell
$env:API_LOG_PATH = 'logs/api.log'
$env:API_SEED = '2026'
.venv/Scripts/python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --workers 1 --no-access-log
```

En otra terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/healthz
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/purchases -ContentType 'application/json' -Body '{"coupon_id":"demo-coupon-001","quantity":1}'
```

Una petición válida puede devolver 400 o 503 deliberadamente. `/healthz` siempre responde 200 mientras el proceso funciona. `/openapi.json` documenta las rutas y los esquemas de entrada; `/docs` y `/redoc` están deshabilitados. Detener Uvicorn con Ctrl+C.

## Configuración

Las variables se leen al crear la aplicación. Para cambiar un perfil, reiniciar el proceso; no hay cambios globales de entorno ni archivo `.env` cargado automáticamente.

| Variable | Predeterminado | Significado |
| --- | --- | --- |
| `API_LOG_PATH` | `logs/api.log` | Ruta absoluta o relativa al directorio de ejecución |
| `API_SEED` | No fijada | Entero opcional para los sorteos del proceso |
| `API_SCENARIO` | `normal` | Escenario predeterminado: `normal` o `qr-degraded` |
| `API_SUCCESS_RATE` | `0.90` | Probabilidad 2xx normal |
| `API_CLIENT_ERROR_RATE` | `0.05` | Probabilidad 400 normal |
| `API_SERVER_ERROR_RATE` | `0.05` | Probabilidad 503 normal |
| `API_LATENCY_MIN_MS` / `API_LATENCY_MAX_MS` | `80` / `350` | Demora uniforme normal, ms |
| `QR_SUCCESS_RATE` | `0.60` | Probabilidad 2xx en QR degradado |
| `QR_CLIENT_ERROR_RATE` | `0.10` | Probabilidad 400 en QR degradado |
| `QR_SERVER_ERROR_RATE` | `0.30` | Probabilidad 503 en QR degradado |
| `QR_LATENCY_MIN_MS` / `QR_LATENCY_MAX_MS` | `300` / `900` | Demora uniforme QR degradado, ms |

Cada tripleta debe sumar 1, con tolerancia 1e-9. Se rechazan NaN, infinitos, probabilidades negativas, latencias negativas, mínimo mayor al máximo y máximo superior a 10000 ms. La aplicación no inicia con configuración inválida o un archivo de logs inaccesible.

La cabecera `X-Simulation-Scenario: qr-degraded` selecciona el escenario por petición, también disponible con `--scenario` del generador. Solo emisión y canje de QR cambian al perfil QR; los otros seis endpoints mantienen el perfil normal. Una cabecera inválida devuelve 422 en rutas de negocio y no altera `/healthz`.

Las proporciones son probabilidades configuradas, no porcentajes garantizados por muestra. La semilla reproduce los sorteos con el mismo orden de llamadas; no reproduce tiempos reales ni el orden de finalización bajo concurrencia. Los 422 por entradas inválidas y 404/405 de enrutamiento quedan fuera del sorteo.

## Logs automáticos y trazabilidad

`api/main.py` instrumenta el flujo ASGI: comienza con `perf_counter_ns()`, observa el código enviado y registra una línea JSON UTF-8 al terminar de enviar el cuerpo. No usa la demora sorteada como duración. `event.duration` es un entero en nanosegundos; dividir por 1000000 para milisegundos. El tiempo incluye validación, simulación y envío ASGI, pero excluye el viaje de red completo del cliente y la posterior escritura del log.

Cada respuesta terminada, incluidos salud, validación, 404, 405 y errores inesperados 500, produce una línea; una conexión cancelada antes de completar respuesta no demuestra una respuesta finalizada. La cabecera `X-Request-ID` coincide con `request_id` en el cuerpo de negocio y en el log. `event.id` es distinto y único para cada evento. El esquema completo de claves literales con puntos está en el contrato.

No se registran cuerpos, queries, cookies, cabeceras de entrada, IPs, tokens ni traceback. Los errores de validación no devuelven los valores rechazados. `url.path` guarda la ruta solicitada sin query: no colocar información sensible en nombres de rutas. Usar únicamente datos ficticios. Un error inesperado anterior al envío de cabeceras se convierte en 500 con mensaje fijo. Un fallo de transporte después de empezar una respuesta no puede cambiar su código y se propaga al servidor.

El escritor abre en modo append y hace flush por línea; reiniciar conserva los registros existentes. No hace `fsync` por evento ni garantiza persistencia frente a un corte abrupto del sistema operativo. No hay rotación automática: el archivo crece mientras corre el generador. Para esta práctica, detener API y tráfico antes de archivar un log y reiniciar. El equipo debe decidir y validar la rotación y recolección que use posteriormente. Los errores de escritura se propagan; no se oculta una pérdida de evidencia.

Ejecutar un solo worker por archivo. No compartir una ruta entre varios procesos de API; el bloqueo protege escrituras dentro del mismo proceso. El archivo de muestra final está separado de los logs temporales de pruebas.

## Pruebas locales realmente ejecutadas

Se ejecutó en Python 3.13.5:

```powershell
.venv/Scripts/python.exe -m pytest api/tests -q --basetemp=.pytest_cache/api-local --tb=short
```

Resultado observado: **57 passed, 1 warning in 1.20s**. La advertencia proviene de Starlette 1.10.0: su `TestClient` depreca el uso interno de httpx; las pruebas pasan con httpx 0.28.1. No se añadió otra biblioteca solo para ocultar la advertencia.

Se verifican las ocho rutas en 2xx/400/503, metadatos/códigos/IDs, tipos y zona UTC, duración real y variación, perfiles inválidos, sorteos con semilla, degradación restringida a QR, salud estable, privacidad de errores, JSON inválido, 404/405/500 sin duplicados, OpenAPI sin UI y conservación append. La prueba estadística usa 20000 sorteos en memoria; no se presenta como evidencia de tráfico HTTP ni como resultado del monitoreo.

Los primeros intentos en el sandbox se bloquearon creando sockets internos de asyncio. Al ejecutar fuera del sandbox, el directorio temporal predeterminado de pytest produjo un error de permisos; el comando exitoso anterior usó una ruta temporal dentro del proyecto. Esos intentos no se cuentan como pruebas aprobadas. La integración TCP con generador y su resultado final se documentan en [qa-api-traffic.md](qa-api-traffic.md).

## Pendiente: validación con Docker

`api/Dockerfile` está preparado y revisado como texto, **no construido ni ejecutado**. Parte de `python:3.13-slim`, fija versiones directas en `api/requirements.txt`, usa UID/GID 10001 y ejecuta Uvicorn como proceso principal sin shell. La etiqueta base puede actualizarse; el equipo decidirá el digest al validar las imágenes. El contexto previsto es la raíz del repositorio.

Interfaces para la configuración propia del equipo:

- Servicio sugerido `api`, puerto interno TCP 8000; escucha `0.0.0.0` en el contenedor.
- Log en `/app/logs/api.log` mediante `API_LOG_PATH`; directorio creado con propietario 10001:10001.
- El volumen montado debe permitir escritura a ese UID/GID y lectura al recolector; los permisos incluidos en la imagen no garantizan los del volumen montado.
- Montar el mismo contenido de logs en solo lectura para Filebeat según la configuración que escriba el equipo.
- Generador en la misma red: `API_BASE_URL=http://api:8000`; no requiere credenciales.
- Salud de proceso disponible en `GET /healthz`; no demuestra disponibilidad funcional de compra/canje.

Después de instalar Docker, el equipo debe construir la imagen, comprobar instalación de dependencias y arranque sin root, acceso a puerto 8000 desde otro contenedor, parada con señales, escritura y persistencia de volumen tras reiniciar, y comportamiento ante permisos incorrectos. También quedan pendientes Filebeat, Elasticsearch, Heartbeat, las seis visualizaciones y las evidencias de Kibana. No se creó configuración de esos componentes ni se ejecutó ningún comando Docker.
