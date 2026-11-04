# Contrato de API y generador — CupónManía Fase 3

Contrato v1 fijado por el coordinador antes del desarrollo paralelo. Fuente del catálogo: sección 3 de `docs/sources/fase-1.md`; componentes de Fase 2 según `docs/fase-3/instructions.md`, sección 4.2. Todas las operaciones son ficticias, sin estado transaccional, pagos, cuentas ni tickets Jira reales.

## Endpoints

Base local: `http://127.0.0.1:8000`. Cuerpos JSON obligatorios para POST; campos adicionales se rechazan. Identificadores: cadenas de 1–64 caracteres, únicamente letras ASCII, números, guion y guion bajo. Usar prefijo `demo-` en los datos del generador. `quantity` es entero de 1 a 10. `action` solo admite los valores indicados.

| Catálogo / categoría | Método y ruta | Componente | Entrada válida de ejemplo | Éxito / data |
| --- | --- | --- | --- | --- |
| INC-01 / Incidente | POST `/api/v1/purchases` | Compras y pagos | `{"coupon_id":"demo-coupon-001","quantity":1}` | 201 / `{"purchase_id":"demo-purchase","status":"purchased"}` |
| INC-02 / Incidente | POST `/api/v1/coupons/issue` | QR y canje | `{"purchase_id":"demo-purchase-001"}` | 201 / `{"coupon_id":"demo-coupon","qr_code":"demo-qr","status":"issued"}` |
| INC-03 / Incidente | POST `/api/v1/coupons/redeem` | QR y canje | `{"qr_code":"demo-qr-001","merchant_id":"demo-merchant-001"}` | 200 / `{"status":"redeemed"}` |
| INC-04 / Incidente | GET `/api/v1/platform/status` | Plataforma | Sin cuerpo | 200 / `{"status":"operational"}` |
| SR-01 / Solicitud de servicio | POST `/api/v1/merchants` | Comercios | `{"merchant_id":"demo-merchant-001","action":"create"}` (`create` o `update`) | 201 / `{"status":"accepted"}` |
| SR-02 / Solicitud de servicio | POST `/api/v1/promotions` | Promociones | `{"promotion_id":"demo-promotion-001","merchant_id":"demo-merchant-001","action":"publish"}` (`publish` o `update`) | 201 / `{"status":"accepted"}` |
| SR-03 / Solicitud de servicio | POST `/api/v1/accounts/recovery` | Cuentas y accesos | `{"account_id":"demo-account-001","action":"unlock"}` (`unlock` o `reset`) | 200 / `{"status":"accepted"}` |
| SR-04 / Solicitud de servicio | POST `/api/v1/refunds` | Reembolsos | `{"purchase_id":"demo-purchase-001","action":"refund"}` (`refund` o `cancel`) | 200 / `{"status":"accepted"}` |

La salida de éxito tiene la forma siguiente (los IDs de la tabla son datos ficticios de salida, no referencias persistentes):

```json
{"synthetic":true,"request_id":"UUID generado por el servidor","catalog_item":"INC-01","component":"Compras y pagos","scenario":"normal","outcome":"success","data":{"purchase_id":"demo-purchase","status":"purchased"}}
```

Un error simulado 4xx devuelve HTTP 400 y `outcome: "client_error"`; uno 5xx devuelve HTTP 503 y `outcome: "server_error"`. Ambos conservan los metadatos del sobre y reemplazan `data` por `error: {"code":"simulated_client_error|simulated_server_error","message":"mensaje fijo sin datos de entrada"}`. La cabecera de respuesta `X-Request-ID` contiene el UUID generado por el servidor. Validación real inválida devuelve 422, ruta inexistente 404 y método incorrecto 405: no forman parte del sorteo probabilístico. No reflejar cuerpos, valores inválidos ni secretos en errores o logs.

`GET /healthz` siempre devuelve 200 con `{"status":"ok","synthetic":true}`, sin fallos ni demoras simuladas. Solo verifica vida del proceso, no éxito funcional. Mantener `/openapi.json`; desactivar `/docs` y `/redoc` para no ofrecer UI adicional.

## Perfiles y configuración de API

Python 3.13; FastAPI, Uvicorn, httpx y pytest. Entrypoint `api.main:app`, factory `api.main.create_app()` para aislamiento de pruebas; el entorno se lee al crear la app. Un proceso / un worker por archivo de logs.

| Variable | Predeterminado | Regla |
| --- | --- | --- |
| `API_LOG_PATH` | `logs/api.log` | Archivo UTF-8 NDJSON append, crear directorio padre |
| `API_SEED` | sin semilla | Entero opcional para RNG local al proceso |
| `API_SCENARIO` | `normal` | `normal` o `qr-degraded` |
| `API_SUCCESS_RATE` | `0.90` | Probabilidad finita entre 0 y 1 |
| `API_CLIENT_ERROR_RATE` | `0.05` | Probabilidad finita entre 0 y 1 |
| `API_SERVER_ERROR_RATE` | `0.05` | Probabilidad finita entre 0 y 1 |
| `API_LATENCY_MIN_MS` / `API_LATENCY_MAX_MS` | `80` / `350` | Finitos, 0 ≤ min ≤ max ≤ 10000 |
| `QR_SUCCESS_RATE` / `QR_CLIENT_ERROR_RATE` / `QR_SERVER_ERROR_RATE` | `0.60` / `0.10` / `0.30` | Mismas reglas |
| `QR_LATENCY_MIN_MS` / `QR_LATENCY_MAX_MS` | `300` / `900` | Mismas reglas |

Cada tripleta de probabilidades suma 1 (tolerancia 1e-9); configuración inválida impide iniciar. Para peticiones válidas, sortear clase HTTP y demora uniforme; medir después el tiempo efectivamente transcurrido. `X-Simulation-Scenario` puede seleccionar por petición `normal` o `qr-degraded`; un valor inválido devuelve 422 sin copiarlo a los logs. El perfil QR solo altera INC-02 e INC-03; los demás usan probabilidades y latencia normales, aunque conservan el escenario seleccionado como metadato. Salud no depende de la cabecera. La semilla de API reproduce sorteos solo con igual orden de llamadas; concurrencia y reloj impiden prometer tiempos idénticos.

## Log producido exclusivamente por la API

Una línea JSON plana por respuesta HTTP finalizada, también 422/404/405 y salud. Sin cuerpos, parámetros query, cookies, tokens, IPs ni cabeceras de entrada. Medición con `time.perf_counter_ns()` desde entrada HTTP hasta envío de la respuesta, sin convertir una demora configurada en duración ficticia. Errores inesperados controlados producen 500 y una sola línea sin traceback ni datos sensibles. No duplicar logs de acceso de Uvicorn (arranque con `--no-access-log`).

| Clave literal JSON | Tipo / valor |
| --- | --- |
| `@timestamp` | Cadena UTC ISO 8601 con zona |
| `http.request.method` | Cadena, método real |
| `http.response.status_code` | Entero, código enviado |
| `event.duration` | Entero positivo, nanosegundos medidos |
| `url.path` | Ruta sin query |
| `service.name` | `cuponmania-api` |
| `log.level` | `INFO` para <400, `WARN` para 4xx, `ERROR` para 5xx |
| `event.id` | UUID único por registro |
| `request_id` | UUID generado por el servidor, igual al de respuesta |
| `catalog_item` | INC-01…INC-04 / SR-01…SR-04; null fuera del catálogo |
| `component` | Componente de la tabla; null fuera del catálogo |
| `scenario` | `normal`, `qr-degraded` o `health`/`unmatched` fuera del catálogo |
| `cuponmania.synthetic` | Booleano true |

Estos son nombres literales con puntos, no objetos anidados. El equipo decidirá su mapeo en la recolección. `event.duration / 1000000` da milisegundos. Sin rotación automática en esta iteración: documentar crecimiento y coordinar cualquier rotación externa con la recolección. Fallar al iniciar si el archivo no puede abrirse; nunca aparentar evidencia persistida cuando la escritura falla.

## Generador

Entrypoint `python -m traffic.main`. Opciones: `--base-url` (entorno `API_BASE_URL`, por defecto `http://127.0.0.1:8000`), `--rate` (2 req/s, >0 y ≤20), `--concurrency` (2, entero 1–16), `--timeout` (5 s, >0 y ≤60), `--duration` (segundos positivos) o `--count` (entero positivo), `--seed` (entero), `--mode` (`random` o `sequential`, predeterminado random), `--scenario` (`normal` o `qr-degraded`). Sin duración/cantidad funciona hasta Ctrl+C; límites mutuamente excluyentes.

Cada ciclo visita los ocho endpoints: en modo secuencial en el orden de la tabla, en random mediante permutación aleatoria de cada ciclo. Variar IDs ficticios. No depender de llamadas exitosas previas. La semilla reproduce solicitudes con igual configuración, no resultados de red. Mantener tasa global limitada, concurrencia acotada y memoria acotada; no acumular tareas sin límite. Duración limita admisión, luego drena peticiones activas dentro del timeout. Ctrl+C/SIGTERM detiene admisión, drena/cancela limpiamente, cierra cliente y emite resumen. 4xx/5xx/timeouts/caída temporal no detienen el ciclo y no provocan reintentos sin límite.

Solo destinos HTTP locales `localhost`, IP loopback o nombre exacto `api` para la futura red de Compose; rechazar destinos de terceros, credenciales, query, fragmento y prefijo de ruta en URL base; no seguir redirecciones ni proxies del entorno. No escribir logs del servidor ni documentos Elasticsearch. Resumen propio JSON en stdout con al menos `attempted`, `completed`, `transport_errors`, `status_counts`, `endpoint_counts` y duración real. Dockerfile del generador recibe `API_BASE_URL=http://api:8000` al integrarse.

## Dockerfiles e integración prevista

Ambos Dockerfiles usan contexto de construcción raíz del repositorio, imagen oficial Python 3.13 slim, dependencias fijadas y usuario no root UID/GID 10001. API escucha `0.0.0.0:8000` y usa `API_LOG_PATH=/app/logs/api.log`; preparar directorio con permisos del usuario. Generador acepta argumentos CLI mediante ENTRYPOINT en forma exec. No crear Compose ni configuración de observabilidad. No ejecutar ningún comando Docker; documentar validación pendiente de imágenes, red, permisos, persistencia y señales.

## Propiedad de archivos

Coordinador: este contrato, configuración de pruebas/dependencias compartidas, SETUP y bitácora de IA, evidencia final. `api_builder`: `api/` y `docs/api.md`. `traffic_builder`: `traffic/` y `docs/traffic.md`. `api_qa`: `tests/integration/` y `docs/qa-api-traffic.md`, tras completar ambos módulos. Cambios de contrato se coordinan antes de modificarlo. Sin UI, infraestructura ELK/Heartbeat, análisis de monitoreo, commits ni pushes.
