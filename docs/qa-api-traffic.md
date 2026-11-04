# Verificación local de API y tráfico

Realizada el **3 de noviembre de 2026, Guatemala**, con Python **3.13.5** del entorno `.venv`, pytest **9.2.0**, FastAPI **0.162.0**, Uvicorn **0.54.0** y httpx **0.28.1**. API y generador fueron implementados en paralelo después de fijar `docs/contracts.md`; `api_qa` trabajó cuando ambos módulos quedaron listos. No se utilizó Docker.

## Pruebas realmente ejecutadas

Todos los comandos se ejecutan desde la raíz del repositorio:

| Comando | Resultado observado | Responsable |
| --- | --- | --- |
| `.venv/Scripts/python.exe -m pytest api/tests -q --basetemp=.pytest_cache/api-local --tb=short` | 57 passed, 1 warning in 1.20s | `api_builder` |
| `.venv/Scripts/python.exe -m pytest traffic/tests -q` | 54 passed in 1.94s | `traffic_builder` |
| `.venv/Scripts/python.exe -m pytest tests/integration -q --basetemp=.pytest_cache/integration-local --tb=short` | 8 passed in 18.42s | `api_qa` |
| `.venv/Scripts/python.exe -m pytest -q --basetemp=.pytest_cache/full-local --tb=short` | **119 passed, 1 warning in 21.48s**, salida 0 | Coordinador, verificación final |

La salida íntegra de la suite completa está en `evidencias/pruebas-locales.txt`. El coordinador conservó stdout/stderr mediante `Tee-Object`; son 57 pruebas de API, 54 del generador y 8 integradas. El archivo de muestra mantuvo su SHA-256 después de esta ejecución.

Los primeros intentos de unitarias dentro del aislamiento de la herramienta se bloquearon al crear `socketpair` de asyncio en Windows, antes de atender solicitudes. Otro intento de API encontró permisos insuficientes en el directorio temporal predeterminado. Los procesos de esos intentos se detuvieron; no se cuentan como pruebas aprobadas. Las ejecuciones exitosas usaron permiso para procesos y sockets locales; API e integración usaron un directorio temporal dentro del proyecto. No se instalaron herramientas globales ni se modificó el Python 3.7 utilizado por otro proyecto.

La advertencia es de Starlette `TestClient`: depreca su uso interno de httpx. No hubo pruebas fallidas en las ejecuciones exitosas indicadas; esta advertencia no es una validación de compatibilidad futura. Las pruebas integradas usan HTTP sobre TCP y procesos CLI reales, sin `TestClient` ni transporte simulado.

## Qué se comprobó

- **API unitaria:** ocho rutas en éxito/400/503, entradas válidas e inválidas, configuración probabilística, semilla, duración real variable en nanosegundos, metadatos del catálogo y componentes, salud estable, 422/404/405/500, privacidad y una línea por respuesta. También append, fallo de inicio por log inaccesible y OpenAPI sin UI. El ensayo de 20000 sorteos en memoria comprueba probabilidades; no es evidencia HTTP del monitoreo.
- **Generador unitario:** cobertura de ocho rutas por ciclo, datos ficticios, semilla, límites y argumentos, tasa global, concurrencia, timeouts, continuidad ante errores, duración, drenaje y callback de SIGINT. Estas pruebas usan transporte controlado; no reemplazan la integración TCP.
- **Integración:** Uvicorn se inicia en un proceso local con puerto disponible y un log temporal por prueba. Los ocho endpoints se solicitan mediante TCP con perfiles forzados 100% éxito, 100% 400 y 100% 503. Cada respuesta se correlaciona por `X-Request-ID` con exactamente un evento y su código, método y ruta. Se validan los siete campos, tipos, UTC, IDs únicos, catálogo/componente, nivel y duración real.
- **CLI con 64 solicitudes reales:** ocho por endpoint, resumen coincidente con los códigos y rutas del log, sin errores de transporte. Esta prueba usa un perfil 50%/25%/25% y latencias reducidas para cubrir clases HTTP rápidamente; no cambia los valores predeterminados ni la muestra final.
- **Escenarios y límites:** una ejecución TCP limitada por duración verifica que solo emisión/canje QR usan el perfil degradado. Se verifican 422/404/405 reales sin copiar entradas sensibles al log o respuesta.
- **Caída y recuperación:** el generador sigue activo mientras se detiene el proceso API y se reinicia en el mismo puerto. El resumen incluye errores de transporte y respuestas completadas antes/después; el archivo de logs conserva registros del primer proceso y del reinicio.
- **Modo continuo y señal:** un proceso hijo ejecuta el CLI sin `--count` ni `--duration`; un temporizador entrega `SIGINT` mediante `signal.raise_signal`. Se observan solicitudes TCP completadas, resumen `stop_reason=stopped`, ninguna cancelación pendiente y código de salida **0**. Esto prueba la señal en el proceso, no una pulsación física de teclado.

Los procesos de prueba se cierran en bloques `finally`. La terminación del proceso API durante limpieza/caída es controlada por la prueba; no se presenta como comprobación de parada de contenedores.

## Ctrl+C real en terminal

El coordinador ejecutó en una terminal PTY:

```powershell
.venv/Scripts/python.exe -m traffic.main --base-url http://127.0.0.1:9 --rate 2 --timeout 0.5 --duration 30
```

Después envió Ctrl+C. El generador terminó a los **15.1495813 s**, antes del límite de 30 s, e imprimió un resumen con `attempted=29`, `completed=0`, `transport_errors=29`, `cancelled=0` y `stop_reason=stopped`. El destino era loopback sin API; los fallos observados fueron timeouts. La sesión PowerShell informó estado 1 por la interrupción de terminal: esa prueba no se usa para afirmar el código de salida nativo de Python. El código 0 citado arriba procede de la prueba automatizada del proceso hijo.

## Muestra final de logs auténticos

El coordinador ejecutó Uvicorn en un hilo local con socket **TCP loopback**, un worker y cierre mediante `should_exit`; el generador se ejecutó como subproceso independiente. No se usó un cliente ASGI en memoria. Ventana registrada: `2026-11-04T04:41:13.581784Z` a `2026-11-04T04:41:33.489554Z`, equivalente al **3 de noviembre, 22:41**, en Guatemala.

Archivos conservados, sin edición de líneas:

- `evidencias/api-local.log`: **64 registros JSON auténticos**, ocho por cada endpoint; sin peticiones de salud en esta muestra.
- `evidencias/generador-local.json`: stdout real del generador: 64 intentos y 64 respuestas completadas, cero errores de transporte/cancelaciones, duración **19.0222921 s**.
- `evidencias/ejecucion-local.json`: comando, entorno, ventana temporal, conteos y SHA-256.

Comando del generador registrado en los metadatos (el puerto fue asignado para esa ejecución):

```powershell
.venv/Scripts/python.exe -m traffic.main --base-url http://127.0.0.1:51146 --count 64 --rate 4 --concurrency 1 --mode sequential --seed 20261103 --scenario normal
```

La API usó `API_SEED=20261103`, `API_SCENARIO=normal`, probabilidades `0.90/0.05/0.05`, latencias configuradas **80–350 ms** y `API_LOG_PATH` apuntando a `evidencias/api-local.log`. Los pasos para repetir el flujo con otro archivo están en `SETUP.md`; la API añade líneas si el archivo ya existe.

| Clase | Probabilidad configurada | Conteo observado | Porcentaje observado |
| --- | ---: | ---: | ---: |
| 2xx | 90% | 57 (200: 27; 201: 30) | 89.0625% |
| 4xx | 5% | 4 (400) | 6.25% |
| 5xx | 5% | 3 (503) | 4.6875% |

Son conteos de verificación de software de esta muestra, no un análisis del comportamiento real de CupónManía ni de sus SLO. Las probabilidades configuradas no garantizan porcentajes exactos en una muestra finita. Ningún registro se añadió o ajustó para alcanzar una distribución.

`api_qa` verificó en modo lectura las **64 líneas** y el SHA-256 del archivo:

```text
150cec1f98537db63064872fc398112723a5b0184f1ed2b7a06eb795d516057e
```

Comandos de esa comprobación:

```powershell
Get-FileHash evidencias/api-local.log -Algorithm SHA256
(Get-Content evidencias/api-local.log | Measure-Object -Line).Lines
```

El coordinador comprobó además 64 IDs únicos de evento y petición, duración positiva y coincidencia exacta de los conteos del archivo con el stdout del generador. La muestra y sus metadatos no demuestran ingesta ni disponibilidad en ELK.

## Pendiente: validación con Docker

Los Dockerfiles se prepararon y revisaron como texto; **no se instaló Docker, no se invocó ningún comando Docker, no se descargaron/construyeron imágenes ni se ejecutaron contenedores**.

- [ ] Construcción de `api/Dockerfile` y `traffic/Dockerfile` desde el contexto raíz e instalación de sus dependencias en Linux.
- [ ] Arranque como UID/GID 10001, conectividad entre contenedores y resolución de `api:8000` con `API_BASE_URL`.
- [ ] Permisos y persistencia real del volumen de logs, incluidos reinicios/recreación, y acceso de solo lectura del recolector.
- [ ] Manejo de señales, margen de apagado y caída/recuperación entre contenedores.
- [ ] Configuración propia de Compose y recolección Filebeat/Logstash, ingesta sin duplicados y almacenamiento/tipos de campos en Elasticsearch.
- [ ] Configuración y evidencia up/down de Heartbeat.
- [ ] Seis visualizaciones y captura completa de Kibana, interpretación del equipo e informe final con declaración de IA.

La implementación local de API/tráfico está verificada dentro del alcance descrito. **La Fase 3 no está terminada**: infraestructura, dashboard, análisis y evidencias del stack siguen a cargo del equipo.

## Inventario de entregables de esta iteración

| Archivos creados | Para qué sirven |
| --- | --- |
| `api/__init__.py`, `api/main.py`, `api/config.py`, `api/catalog.py`, `api/requirements.txt` | API simulada, instrumentación, perfiles y catálogo |
| `traffic/__init__.py`, `traffic/main.py`, `traffic/requirements.txt` | Generador HTTP continuo/finito y dependencia |
| `api/Dockerfile`, `traffic/Dockerfile`, `.dockerignore` | Preparación de imágenes; validación Docker pendiente |
| `api/tests/test_api.py`, `traffic/tests/test_traffic.py`, `tests/integration/test_http_flow.py` | Pruebas unitarias e integración TCP |
| `pytest.ini`, `requirements-dev.txt` | Descubrimiento de pruebas y dependencias de desarrollo |
| `docs/contracts.md`, `docs/api.md`, `docs/traffic.md`, `docs/qa-api-traffic.md` | Contrato, uso y resultados reproducibles |
| `evidencias/api-local.log`, `evidencias/generador-local.json`, `evidencias/ejecucion-local.json`, `evidencias/pruebas-locales.txt` | Eventos auténticos, resumen, trazabilidad y pruebas ejecutadas |

Se actualizaron `SETUP.md` (ejecución local e interfaces para el equipo), `.gitignore` (caché local) y `docs/uso-de-ia.md` (asistencia recibida). `.venv` y `.uv-cache` son archivos locales ignorados; no forman parte del código entregable. `README.md`, `LICENSE` y los documentos fuente se conservaron. No se crearon ni editaron Compose, configuración ELK/Heartbeat, dashboard o UI propia.
