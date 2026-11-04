# Generador continuo de tráfico de CupónManía

El módulo `traffic.main` realiza peticiones HTTP a los ocho endpoints de `docs/contracts.md`, con datos ficticios que comienzan por `demo-`. No crea tickets Jira, no escribe el archivo de logs de la API y no envía documentos a Elasticsearch. Solo la API produce los eventos que recolectará el equipo.

## Ejecución local

Requiere Python 3.13 y las dependencias de `traffic/requirements.txt`. Desde la raíz del repositorio, con el entorno del proyecto preparado según `docs/fase-3/SETUP.md` y la API escuchando en el puerto 8000:

```powershell
.venv/Scripts/python.exe -m traffic.main
```

Sin límite de tiempo o cantidad, se ejecuta hasta Ctrl+C. Ejemplo finito que visita cada endpoint ocho veces:

```powershell
.venv/Scripts/python.exe -m traffic.main --count 64 --rate 5 --concurrency 2 --mode sequential --seed 42
```

Ejemplo de escenario QR durante 30 segundos:

```powershell
.venv/Scripts/python.exe -m traffic.main --duration 30 --rate 4 --concurrency 2 --scenario qr-degraded --seed 42
```

La opción `--scenario` envía `X-Simulation-Scenario` a la API. El generador no decide los códigos ni la demora del servidor: la API aplica sus probabilidades normales (90 % éxito, 5 % 4xx y 5 % 5xx por defecto) o la degradación de QR. La semilla del generador reproduce el orden y los cuerpos; la semilla independiente `API_SEED` controla los sorteos de la API. No se garantizan tiempos de red idénticos ni porcentajes observados iguales a los configurados.

## Parámetros

| Opción | Valor por defecto | Restricción / comportamiento |
| --- | --- | --- |
| `--base-url` | `API_BASE_URL` o `http://127.0.0.1:8000` | HTTP a `localhost`, IP loopback o nombre exacto `api` |
| `--rate` | `2` | Peticiones por segundo; finito, >0 y ≤20 |
| `--concurrency` | `2` | Máximo de peticiones simultáneas, entero entre 1 y 16 |
| `--timeout` | `5` | Segundos máximos por petición, finito, >0 y ≤60 |
| `--count` | Sin límite | Número entero positivo de intentos, incluyendo fallos de transporte |
| `--duration` | Sin límite | Segundos positivos y finitos de admisión de nuevas solicitudes |
| `--seed` | Aleatoria | Entero para reproducir solicitudes |
| `--mode` | `random` | `random` o `sequential` |
| `--scenario` | `normal` | `normal` o `qr-degraded` |

`--count` y `--duration` son mutuamente excluyentes. CLI tiene precedencia sobre `API_BASE_URL`. Se rechazan credenciales, prefijos de ruta, query y fragmentos en la URL, destinos externos, HTTPS y números de puerto inválidos. No se siguen redirecciones y `trust_env=False` impide usar proxies del entorno. El nombre `api` está reservado para el servicio local que el equipo creará en su red de Compose; no se acepta un hostname arbitrario.

## Cobertura, tasa y fallos

Cada ciclo de ocho solicitudes visita una vez cada endpoint. `sequential` sigue el orden del contrato; `random` mezcla el orden dentro de cada ciclo usando la semilla. Los identificadores y las acciones varían sin depender de una compra previa exitosa. Una ejecución inferior a ocho intentos puede quedar sin cubrir parte del catálogo.

La tasa se aplica globalmente entre admisiones, no por trabajador. No hay ráfaga inicial ni recuperación de solicitudes atrasadas mediante ráfagas. Si se alcanza la concurrencia máxima, se espera un espacio; por ello la tasa real puede ser menor que la solicitada. Solo se mantienen hasta `concurrency` tareas activas y contadores de tamaño acotado. Se descartan los cuerpos de respuesta al leerlos, sin almacenarlos ni volcarlos al resumen.

Las respuestas 4xx y 5xx cuentan como respuestas HTTP completadas. Timeouts, conexiones rechazadas o caídas temporales suman `transport_errors`; no interrumpen los siguientes intentos y no generan reintentos adicionales ocultos. Cada petición tiene un límite total con `asyncio.timeout`, además de los límites de I/O de HTTPX. Esto también evita que un servidor que envía lentamente mantenga la ejecución indefinidamente. El cierre por Ctrl+C/SIGTERM deja de admitir tráfico, espera las peticiones activas dentro de ese límite, cierra el cliente y emite el resumen. En Windows, cerrar forzosamente el proceso desde el administrador de tareas no equivale a Ctrl+C y no garantiza un resumen.

Al acabar la duración se drenan las solicitudes activas, por lo que el tiempo total puede superar `--duration` hasta aproximadamente `--timeout`. No se impone un máximo de memoria proporcional a la duración o al número de solicitudes: no se guarda un historial de respuestas.

## Resumen propio del generador

Se imprime una línea JSON a stdout al terminar. Puede redirigirse a un archivo de evidencia separado; no es el `.log` de la API ni sustituye su evidencia.

| Campo | Significado |
| --- | --- |
| `attempted` | Solicitudes admitidas |
| `completed` | Respuestas HTTP leídas, incluyendo 4xx/5xx |
| `transport_errors` | Intentos sin respuesta completada por timeout o transporte |
| `cancelled` | Tareas canceladas externamente; cierre normal drena las activas |
| `status_counts` | Conteo por código HTTP, claves JSON de cadena |
| `endpoint_counts` | Intentos por ruta, incluso si falla el transporte |
| `transport_error_counts` | Desglose `timeout` / `transport`, sin mensajes sensibles |
| `duration_ns` / `duration_seconds` | Duración real monotónica de la ejecución completa |
| `configured_rate` / `scenario` | Configuración usada |
| `stop_reason` | `count`, `duration` o `stopped` (señal o evento de cierre) |

En un cierre normal se cumple `attempted = completed + transport_errors`, y la suma de `status_counts` coincide con `completed`. No se registra un resultado ficticio del servidor cuando falla el transporte. El proceso sale con código 0 cuando completa el trabajo o se detiene limpiamente, aunque la API haya estado caída; para valorar conectividad deben revisarse los contadores. Parámetros inválidos terminan con código 2.

## Pruebas locales

```powershell
.venv/Scripts/python.exe -m pytest traffic/tests -q
```

Las pruebas unitarias usan transporte controlado de HTTPX y eventos asyncio. Comprueban cobertura y semilla, parámetros, protección de destino, formatos HTTP, continuidad tras 4xx/5xx/timeout, tasa global, concurrencia, límite total, duración, drenaje, redirecciones y manejo del callback SIGINT. Estas pruebas no sustituyen las peticiones TCP reales de `tests/integration/`; sus resultados se registran en `docs/qa-api-traffic.md`.

Ejecución local realizada el 3 de noviembre de 2026 (Guatemala), Python 3.13.5 y pytest 9.2.0: **54 passed in 1.94s**. El primer intento dentro del aislamiento de la herramienta quedó bloqueado al crear `socketpair` del event loop de Windows; se detuvo ese intento y se ejecutó el mismo comando con permisos para las pruebas locales, obteniendo el resultado indicado. No se utilizó Docker. La prueba SIGINT invoca el callback instalado; la comprobación del proceso CLI y TCP real corresponde a la integración.

## Integración prevista

`traffic/Dockerfile` está preparado con contexto de construcción en la raíz del repositorio, base oficial `python:3.13-slim`, dependencia directa fijada y usuario no root UID/GID 10001. El entrypoint exec es `python -m traffic.main`, permitiendo pasar las opciones anteriores. El servicio no expone puertos ni necesita un volumen. Su stdout lleva el resumen propio.

El equipo deberá definir un servicio `api` que escuche en el puerto interno 8000 y proporcionar `API_BASE_URL=http://api:8000` al generador dentro de la misma red. El valor por defecto sigue siendo loopback, por seguridad: sin esa variable, loopback dentro del contenedor apuntaría al propio generador. La API debe ser la única escritora de su archivo de logs y la persistencia/recolección corresponden al equipo.

## Pendiente: validación con Docker

No se ejecutó ningún comando Docker ni se construyeron imágenes o contenedores. Después de instalar Docker, el equipo verificará:

- Construcción de la imagen usando `traffic/Dockerfile` y contexto raíz; instalación reproducible de dependencias en Linux.
- Ejecución con UID/GID 10001 y paso de argumentos al entrypoint.
- Resolución del servicio `api`, conectividad al puerto 8000 y `API_BASE_URL` dentro de la red que configure el equipo.
- Continuidad del generador ante caída y recuperación del contenedor API.
- Cierre mediante SIGTERM y margen de apagado suficiente para drenar `--timeout`; stdout con resumen final.
- Persistencia de logs de la API, recolección con Filebeat, almacenamiento en Elasticsearch, Heartbeat y visualizaciones de Kibana, todos pendientes y a cargo del equipo.

Referencia de implementación: cliente [AsyncClient de HTTPX](https://www.python-httpx.org/async/), [timeouts](https://www.python-httpx.org/advanced/timeouts/) y desactivación de [variables de entorno/proxies](https://www.python-httpx.org/environment_variables/).
