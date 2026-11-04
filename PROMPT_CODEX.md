# Prompt para Codex - CupónManía Fase 3 (API simulada y generador)

Actúa como coordinador técnico del repositorio `cuponmania-observability` y organiza el trabajo mediante subagentes cuando estén disponibles.

## Contexto y restricciones importantes

- No tenemos acceso a ninguna API propia de CupónManía. La decisión es construir una **API simulada**, relacionada con los ocho elementos del catálogo definidos en la Fase 1 y utilizados en Jira Service Management durante la Fase 2.
- **Docker todavía NO está instalado en mi computadora.** No intentes instalar Docker o Docker Compose ni ejecutar `docker`, `docker compose`, construir imágenes, descargar imágenes o probar contenedores. **Prepara los Dockerfiles y la integración prevista, pero deja todas las verificaciones con Docker pendientes para cuando yo lo instale.** No afirmes que Docker o el stack funcionan si no se han probado.
- Podemos ejecutar **pruebas locales sin Docker** (por ejemplo, `pytest`, la API y el generador con Python) si el entorno permite instalar dependencias dentro del proyecto y ejecutar esos procesos. Si tampoco es posible, documenta las limitaciones sin inventar resultados.
- No uses ninguna skill de UI ni construyas frontend. El dashboard exigido será diseñado por nuestro equipo directamente en **Kibana**.
- La configuración de Elasticsearch, Filebeat/Logstash, Kibana y Heartbeat, así como las visualizaciones y la interpretación de resultados, son trabajo propio del equipo. No desarrolles ni generes estos componentes.

## 1. Leer documentación y definir contrato

1. Lee `AGENTS.md`, `instructions.md`, `docs/sources/aclaraciones-fase-3.md` y, cuando corresponda, los materiales de las Fases 1 y 2 incluidos en `docs/sources/`.
2. Inspecciona el repositorio antes de crear archivos. Conserva los `README.md`, `LICENSE` y cualquier trabajo existente. No sobrescribas archivos del equipo sin necesidad.
3. Crea `docs/contracts.md` con los ocho endpoints, métodos HTTP, ejemplos de entrada y salida, categorías, identificadores y formato de logs. No confundas estos endpoints de simulación de operaciones del servicio con endpoints de creación de tickets de Jira.
4. Mantén la relación con los componentes de la Fase 2 y la nomenclatura de CupónManía. Los servicios de la API serán simulados y utilizarán únicamente datos ficticios.

## 2. Coordinar subagentes

Utiliza los perfiles de `.codex/agents/`, si la instalación de Codex admite subagentes:

- `api_builder`: desarrolla `api/`, su `Dockerfile`, sus pruebas propias y `docs/api.md`.
- `traffic_builder`: desarrolla `traffic/`, su `Dockerfile`, sus pruebas propias y `docs/traffic.md`.
- `api_qa`: desarrolla `tests/integration/` y `docs/qa-api-traffic.md`, y comprueba la integración local **sin Docker** después de que ambos módulos estén listos.

Como coordinador, fija primero el contrato, asigna archivos sin solapamientos y ejecuta los trabajos independientes en paralelo cuando sea posible. Si no dispones de subagentes reales, informa la limitación y trabaja secuencialmente, sin simular delegaciones.

## 3. Implementar la API simulada

Usa FastAPI, salvo que encuentres una razón técnica justificada para utilizar otra opción. Implementa estos ocho endpoints:

1. `POST /api/v1/purchases` - compra de cupón (INC-01; Compras y pagos).
2. `POST /api/v1/coupons/issue` - pago confirmado y emisión de QR (INC-02; QR y canje).
3. `POST /api/v1/coupons/redeem` - validación y canje QR (INC-03; QR y canje).
4. `GET /api/v1/platform/status` - consulta de disponibilidad funcional (INC-04; Plataforma).
5. `POST /api/v1/merchants` - alta o modificación de comercio (SR-01; Comercios).
6. `POST /api/v1/promotions` - publicación o modificación de cupón (SR-02; Promociones).
7. `POST /api/v1/accounts/recovery` - recuperación de cuenta (SR-03; Cuentas y accesos).
8. `POST /api/v1/refunds` - reembolso o cancelación (SR-04; Reembolsos).

Agrega `GET /healthz` para comprobar que el proceso está vivo; mantenlo estable y sin fallos aleatorios. Este endpoint es auxiliar y no sustituye los ocho del catálogo.

La API debe devolver respuestas 2xx, 4xx y 5xx en proporciones configurables y presentar tiempos de respuesta variables. Como propuesta inicial configurable, utiliza 90 % / 5 % / 5 % y latencias de 80 a 350 ms; **son parámetros elegidos para la simulación, no exigencias del profesor**. Agrega un escenario opcional de degradación de QR, con latencia y tasa de errores más altas, para realizar pruebas de monitoreo.

Cada petición real atendida por un endpoint de negocio debe generar automáticamente un evento JSON válido en un archivo `.log` persistible, sin escribir registros falsos o manuales. Incluye, como mínimo:

- `@timestamp` (fecha y hora en formato válido).
- `http.request.method`.
- `http.response.status_code`.
- `event.duration` (duración real medida en **nanosegundos**).
- `url.path`.
- `service.name`.
- `log.level`.

Añade `request_id`, `catalog_item`, `component` y `scenario` para facilitar la segmentación futura en Kibana. Los códigos HTTP de los logs deben coincidir con las respuestas realmente enviadas. Evita duplicados, datos personales, credenciales y operaciones comerciales reales.

## 4. Implementar el generador de tráfico

Crea un script que haga peticiones HTTP reales, continuas y variadas a los ocho endpoints. Debe permitir configurar URL base, tasa de peticiones, concurrencia máxima, duración o cantidad de peticiones, semilla reproducible y escenarios. Maneja timeouts y errores de transporte sin detener toda la ejecución; finaliza limpiamente con Ctrl+C.

No envíes eventos directamente a Elasticsearch ni fabriques logs desde el generador: los logs que serán recolectados por Filebeat deben proceder del código de la API simulada.

## 5. Preparar Dockerfiles, sin ejecutar Docker

**Prepara obligatoriamente** `api/Dockerfile` y `traffic/Dockerfile`, aun cuando Docker no esté instalado.

- La API debe escuchar en `0.0.0.0` en un puerto interno documentado, preferiblemente `8000`.
- El generador debe utilizar una variable de entorno para la URL de la API: por ejemplo, `API_BASE_URL=http://api:8000` dentro de una futura red de Docker Compose y `http://127.0.0.1:8000` al probar localmente.
- La API debe escribir logs JSON en una ruta configurable como `/app/logs/api.log`, para que después podamos montar un volumen persistente compartido de solo lectura con Filebeat. Documenta rutas, permisos y comportamiento de rotación, si aplica.
- Documenta variables de entorno, puertos, rutas, volúmenes necesarios, dependencias y nombres de servicios que deberá conectar el equipo al crear Docker Compose.
- Usa prácticas básicas de seguridad y reproducibilidad de contenedores, sin añadir complejidad innecesaria.

**Prohibido por ahora:** ejecutar `docker build`, `docker run`, `docker compose up`, `docker pull` o cualquier verificación dentro de contenedores. Tampoco instales Docker. Deja una sección llamada **"Pendiente: validación con Docker"** con los pasos y criterios que nosotros comprobaremos después de instalarlo.

## 6. Pruebas que sí puedes realizar ahora

Escribe pruebas unitarias e integradas para los ocho endpoints, la distribución de respuestas, la generación de logs, los siete campos obligatorios, la duración en nanosegundos, los componentes y el generador. Utiliza la skill de TDD si ya está instalada; no instales skills sin autorización.

Si Python y las dependencias están disponibles, ejecuta las pruebas **sin Docker**. Si es viable, levanta la API localmente y ejecuta el generador contra ella para obtener una muestra auténtica de **al menos 50 eventos** en un archivo `.log`. Documenta qué comandos se ejecutaron y sus resultados observados. No afirmes que pasaron pruebas no ejecutadas y distingue la tasa de error configurada de la tasa observada.

Aunque las pruebas locales pasen, declara explícitamente **pendientes de validación**: construcción de las imágenes, conectividad entre contenedores, persistencia del volumen, ingesta de Filebeat, almacenamiento en Elasticsearch, comprobaciones de Heartbeat y visualizaciones de Kibana.

## 7. Restricciones académicas y archivos reservados al equipo

NO crees ni edites `docker-compose.yml`, `filebeat.yml`, `heartbeat.yml`, `kibana.yml`, configuraciones de Elasticsearch o Logstash, objetos del dashboard, visualizaciones de Kibana, capturas del dashboard ni interpretaciones de los resultados. Tampoco construyas scripts que generen estos archivos o configuraciones indirectamente. Son tareas que haremos nosotros.

No desarrolles UI personalizada, no uses UI UX Pro Max, no crees tickets reales en Jira y no instales software global. No realices commits ni push sin autorización. Registra el uso de IA con honestidad en `docs/uso-de-ia.md` para que el equipo pueda declararlo en el informe final.

## 8. Entregables de esta iteración

1. Código de la API simulada de ocho endpoints y su contrato documentado.
2. Generador continuo de tráfico HTTP y su documentación.
3. `api/Dockerfile` y `traffic/Dockerfile` preparados, pero **no ejecutados ni probados con Docker**.
4. Pruebas automatizadas y resultados reales de las verificaciones locales que sí puedan realizarse.
5. Archivo `.log` real con al menos 50 registros, si puede generarse localmente sin Docker; de lo contrario, explicar por qué queda pendiente.
6. Guía para ejecutar la API y el generador localmente y para integrarlos más adelante en Docker Compose.
7. Resumen de archivos creados, decisiones técnicas, limitaciones y un checklist preciso de las pruebas pendientes cuando Docker esté instalado.

**No des por finalizada la Fase 3.** Después, nosotros configuraremos Docker Compose, Filebeat, Elasticsearch, Heartbeat, Kibana, las seis visualizaciones del dashboard, las evidencias y el informe técnico final.
