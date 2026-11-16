# Verificación de API, tráfico y stack de observabilidad

## Caída, persistencia e ingesta — 2026-11-15

El coordinador ejecutó el ensayo entre **23:47 y 23:55 del 15 de noviembre de 2026, Guatemala** (16 de noviembre, 05:47–05:55 UTC). `api_qa` revisó los JSON, comparó independientemente las exportaciones comprimidas y examinó ambas capturas. No se modificó código de aplicación ni se borraron volúmenes o registros para obtener estos resultados.

La evidencia está en [`evidencias/2026-11-15-pruebas-stack/`](../evidencias/2026-11-15-pruebas-stack/). El protocolo congeló la ventana de eventos `2026-11-10T00:00:00Z ≤ @timestamp < 2026-11-16T05:42:44.477401Z`, con filtros `event.kind=event` y `service.name=cuponmania-api`. La exportación paginada incluye `(_index, _id)`, `_version` y los campos proyectados de timestamp, petición, respuesta, duración, ingesta, ruta, servicio y nivel. Se compararon multiconjuntos completos, no solo conteos.

| Comprobación ejecutada | Resultado verificado | Evidencia |
| --- | --- | --- |
| `docker compose stop api-simulada`, espera monotónica después de la parada y `docker compose start api-simulada` | **45.0003812 s** de espera; el mismo monitor registró `up → down → up`, con **3 chequeos down** y recuperación a `05:49:08.562Z`. Los tres monitores de preproducción aportaron **6 chequeos up** en la ventana del ensayo. | `02-caida.json` |
| `docker compose restart filebeat` | Mismo contenedor con nueva hora de arranque y mismo volumen; **8755 documentos**, **8735 request IDs**, versiones y proyección idénticos antes/después. Un evento HTTP posterior al arranque (`05:49:10.987Z`) llegó a Elasticsearch a `05:50:19.155Z`. | `03-antes-reinicio-filebeat.json.gz`, `04-despues-reinicio-filebeat.json.gz`, `05-reinicio-filebeat.json` |
| Parada de Filebeat, Heartbeat, Kibana y Elasticsearch; `docker compose up -d --force-recreate elasticsearch kibana filebeat heartbeat` | Los cuatro contenedores cambiaron de ID; se conservaron `cuponmania-observability_esdata` y `cuponmania-observability_filebeatdata`. Los **8755 documentos** conservaron IDs, contenido proyectado y `_version=1`; los **11 objetos de Kibana** conservaron contenido y SHA-256, **sin ejecutar kibana-setup ni reimportarlos**. | `06-antes-persistencia.json.gz`, `07-despues-persistencia.json.gz`, `08-persistencia.json` |
| Comprobación posterior a reanudar la ingesta | Un evento de `05:52:10.988Z`, posterior a la reanudación, se ingirió a `05:53:19.726Z`. A `05:55:43.350Z` se volvió a exportar la ventana de control: seguían los mismos **8755 documentos**, todos en versión 1 y con el mismo multiconjunto y SHA-256 que al comienzo. | `08-persistencia.json`, `11-despues-de-reanudar-ingesta.json.gz`, `12-comparacion-final.json` |

SHA-256 de la proyección canónica conservada en todas las comparaciones:

```text
93cd47507f0cbd4126dd2a8351cfd967f1bb7b4e1481dfaa6f49e3fc9ad98be8
```

**Alcance de “sin duplicados nuevos”:** no aparecieron documentos adicionales, cambios de versión ni alteraciones de los campos exportados en la ventana de control, incluso después del avance de la ingesta. No es una garantía de ausencia de duplicados en todo el histórico o en futuras ejecuciones. Los 20 request IDs repetidos ya existían en la línea base: 19 pares tienen timestamps y duraciones diferentes (16 pares 401→200 y 3 pares 200→200); no son duplicados exactos. El par restante contiene mensajes idénticos ya presentes como **dos eventos distintos en CloudWatch**, cuyos `eventId` coinciden con los dos `_id` de Elasticsearch, según `09-id-repetido-origen.json`. No se atribuye su causa al reinicio ni se hizo una deduplicación automática.

La espera de 45 s es la medida del control de parada; no equivale exactamente al tiempo mostrado entre muestras de Heartbeat. La persistencia comprobada corresponde a Elasticsearch, el volumen de Filebeat y los objetos de Kibana: **no** al archivo local de la API simulada tras recrear su contenedor, que no tiene volumen de logs montado y no se recreó en este ensayo.

### Estado para presentación

[`10-estado-final.json`](../evidencias/2026-11-15-pruebas-stack/10-estado-final.json) registra a las **23:54:10 de Guatemala** los cinco servicios activos; Elasticsearch y Kibana con healthcheck `healthy`, Kibana `available` y los **cuatro monitores en up** con chequeos recientes. Elasticsearch reportó `yellow`, dos shards sin asignar y **cero primarios sin asignar** en el nodo único. La consulta de accesos encontró **8864 documentos**, **53 en los últimos cinco minutos** y **cero con alguno de los siete campos obligatorios ausente**. El avance real de Filebeat en este ensayo actualiza la limitación de ingesta anotada en la revisión anterior.

Se observaron los **ocho paneles con datos**, sin avisos de error, y el eje de latencia en milisegundos. [`dashboard-superior.jpg`](../evidencias/2026-11-15-pruebas-stack/dashboard-superior.jpg) y [`dashboard-inferior.jpg`](../evidencias/2026-11-15-pruebas-stack/dashboard-inferior.jpg) son **dos capturas complementarias de viewport**, con rango Last 24 hours; no se presentan como una nueva captura única de página completa.

El entorno quedó **técnicamente preparado para la demostración** en el estado comprobado. Antes de presentar, el equipo debe mantener vigente la sesión SSO, comprobar que siguen llegando datos y revisar el informe y la declaración de IA. Estos resultados no sustituyen esa revisión ni garantizan disponibilidad futura.

El primer intento de preparación devolvió HTTP 400 al enviar un cuerpo al endpoint de refresh. Se conserva en `error-prepare.json`; el coordinador corrigió el helper para enviar POST sin cuerpo y repitió la preparación con éxito antes de las pruebas. No se contabiliza como una caída de los servicios ni como una prueba aprobada.

## Regresión del importador de Kibana — 2026-11-15

`api_qa` añadió `tests/integration/test_kibana_import.py` para comprobar `elk/kibana/import_objects.py`. Se ejecutó:

```powershell
.venv/Scripts/python.exe -m pytest tests/integration/test_kibana_import.py -q --basetemp=.pytest-tmp-kibana-import
```

Resultado real: **8 passed in 2.25s**, salida **0**. La ejecución autorizada fuera del aislamiento usó solo un servidor HTTP controlado en `127.0.0.1` y un puerto local reservado sin escucha para el error de conexión. No se conectó a Kibana, Docker, AWS ni servicios externos.

Cobertura de regresión:

- Importación confirmada de los **11 objetos** actuales: cuerpo multipart íntegro, archivo NDJSON sin cambios, ruta con `overwrite=true`, cabecera `kbn-xsrf`, salida JSON y código 0.
- Una respuesta **HTTP 200** con `success=false` o con errores parciales devuelve código 1 y no imprime una salida de éxito.
- `successCount=11` no basta: confirmaciones faltantes, identificadores duplicados o un objeto ajeno se rechazan.
- Una conexión rechazada devuelve código 1 con diagnóstico; un archivo de origen con duplicados se rechaza antes de enviar HTTP.

No se detectaron defectos en estos casos. Estas pruebas comprueban el cliente y su validación de respuestas; por sí solas no demuestran la importación ni la renderización en un Kibana real.

### Suite completa y comprobaciones del coordinador

El coordinador ejecutó la suite completa: **149 passed, 1 warning in 32.03s**. La salida real está en [`evidencias/2026-11-15-validacion-local/pruebas.txt`](../evidencias/2026-11-15-validacion-local/pruebas.txt), revisada por `api_qa`. La única advertencia es `StarletteDeprecationWarning` por el uso de httpx en `TestClient`; no hubo pruebas fallidas.

En su ejecución local con Docker, el coordinador confirmó **Elasticsearch y Kibana 9.5.5 saludables**, y los servicios Heartbeat y API simulada activos. La importación contra Kibana real terminó con código **0**, `success=true`, `successCount=11`, los **11 identificadores esperados** y sin errores de importación. Este resultado confirma la importación; no sustituye la revisión visual del dashboard ni prueba la llegada de datos nuevos.

**Limitación de esta ejecución:** el usuario informó que SSO solicita contactar con el administrador; no se completó la configuración de un perfil AWS y Filebeat no estaba activo. Por ello **no se verificaron la ingesta reciente desde CloudWatch ni `lastSync`**. Las evidencias históricas se conservan como tales y no se presentan como una comprobación actual de esa conexión. No se añadieron alternativas de ingesta ni nuevas funciones para eludir esta limitación.

## Primera iteración local — 2026-11-03

> Las secciones siguientes conservan la **primera iteración local del 2026-11-03**. Las frases sobre Docker y ELK pendientes describen ese momento, anterior a la ejecución del stack del 2026-11-10. Para el estado actual, ver `docs/elk.md`, `docs/informe-fase-3.md` y `docs/uso-de-ia.md`.

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

La API usó `API_SEED=20261103`, `API_SCENARIO=normal`, probabilidades `0.90/0.05/0.05`, latencias configuradas **80–350 ms** y `API_LOG_PATH` apuntando a `evidencias/api-local.log`. Los pasos para repetir el flujo con otro archivo están en `docs/fase-3/SETUP.md`; la API añade líneas si el archivo ya existe.

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

## Alcance de esta verificación local

Los Dockerfiles se prepararon y revisaron como texto; **no se instaló Docker, no se invocó ningún comando Docker, no se descargaron/construyeron imágenes ni se ejecutaron contenedores**.

- [ ] Construcción de `api/Dockerfile` y `traffic/Dockerfile` desde el contexto raíz e instalación de sus dependencias en Linux.
- [ ] Arranque como UID/GID 10001, conectividad entre contenedores y resolución de `api:8000` con `API_BASE_URL`.
- [ ] Permisos y persistencia real del volumen de logs, incluidos reinicios/recreación, y acceso de solo lectura del recolector.
- [ ] Manejo de señales, margen de apagado y caída/recuperación entre contenedores.
- [ ] Configuración propia de Compose y recolección Filebeat/Logstash, ingesta sin duplicados y almacenamiento/tipos de campos en Elasticsearch.
- [ ] Configuración y evidencia up/down de Heartbeat.
- [ ] Seis visualizaciones y captura completa de Kibana, interpretación del equipo e informe final con declaración de IA.

La implementación local de API/tráfico quedó verificada dentro del alcance descrito. La infraestructura, el dashboard, el análisis y las evidencias del stack se desarrollaron en una iteración posterior, documentada en `docs/uso-de-ia.md`; el equipo todavía debe revisar la entrega final.

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

En esta primera iteración se actualizaron `docs/fase-3/SETUP.md`, `.gitignore` y `docs/uso-de-ia.md`. `.venv` y `.uv-cache` son archivos locales ignorados; no forman parte del código entregable. Compose, la configuración ELK/Heartbeat y el dashboard se agregaron después, en la iteración del 2026-11-10.
