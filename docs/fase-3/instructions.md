# CupónManía - Proyecto Fase 3: Monitoreo (ELK)

## 1. Propósito y documentos fuente

Este archivo proporciona el contexto de las tres fases a Codex y al equipo. Es una guía de requisitos; no demuestra que la Fase 3 ya esté configurada ni sustituye los documentos originales.

Curso: CC3047 - Administración y Mantenimiento de Sistemas, Universidad del Valle de Guatemala, semestre II 2026. Catedrático: Vinicio Paz.

Integrantes: Sergio Orellana (221122), Nelson García Bravatti (22434), Rodrigo Mansilla (22611), Joaquín Puente (22296), Gabriel Paz (221087).

Fuentes:

- `docs/sources/fase-1.md`: diseño original de CupónManía.
- `docs/sources/fase-2.pdf`: implementación del Service Desk CPM.
- `docs/sources/fase-3-instrucciones.pdf`: enunciado de Fase 3, 3 páginas.
- `docs/sources/aclaraciones-fase-3.md`: aclaraciones del usuario sobre API simulada, generador y uso de IA.
- `assets/brand/`: imágenes originales del logotipo (solo para referencias/documentación; no se requiere construir una web).

Las secciones 2 y 3 recogen el enunciado y sus aclaraciones. La sección 4 resume las fases previas. La sección 5 describe decisiones propuestas para este repositorio, no exigencias adicionales del profesor.

## 2. Instrucciones del PDF de Fase 3

### 2.1 Objetivo

Partiendo del servicio de la Fase 1 y del Service Desk de la Fase 2, construiremos un sistema de monitoreo del comportamiento de la API, métricas de desempeño y salud, disponibilidad y tiempos de respuesta. La solución se presenta mediante un **dashboard en Kibana** alimentado con eventos de una API relacionada con CupónManía.

El PDF menciona el stack ELK (Elasticsearch, Logstash y Kibana) y permite recolectar los logs con **Filebeat o Logstash**. Para el entregable de `docker-compose.yml` enumera expresamente Elasticsearch, Kibana, Filebeat y Heartbeat. Para simplificar, el equipo puede optar por Filebeat y documentar la decisión.

### 2.2 Requerimientos técnicos

1. Instalar y configurar el stack de observabilidad y un flujo automático de logs de API hasta Elasticsearch.
2. Recolectar y enviar los logs mediante Filebeat o Logstash.
3. Registrar automáticamente desde el código de la API, como mínimo, estos siete campos: `@timestamp`, `http.request.method`, `http.response.status_code`, `event.duration`, `url.path`, `service.name`, `log.level`.
4. No generar los logs manualmente: deben resultar de peticiones realmente ejecutadas contra la API.
5. Implementar un monitor Heartbeat que compruebe la disponibilidad de los endpoints principales. Si todo corre en el mismo servidor/proyecto, el PDF permite un solo Heartbeat para observar si el ambiente está arriba.
6. Crear dentro de **Kibana** las seis visualizaciones obligatorias: tráfico de peticiones, tiempo de respuesta promedio, estado del sistema (up/down), distribución por códigos HTTP, error rate y top endpoints.

El dashboard debe mostrar información derivada de los logs/Heartbeat reales, no muestras prefabricadas ni el dashboard de Jira de la Fase 2. **No se construirá una UI web adicional:** Kibana es la interfaz de monitoreo y el entregable evaluado.

### 2.3 Entregables

- `docker-compose.yml` funcional que incluya Elasticsearch, Kibana, Filebeat y Heartbeat. Se pueden añadir la API y el generador como servicios de apoyo.
- Archivo `.log` con al menos **50 registros auténticos** producidos automáticamente por la API simulada.
- `heartbeat.yml` funcional.
- Captura del dashboard completo de Kibana.
- Informe técnico con arquitectura, configuración y resultados obtenidos.
- Script generador de tráfico, proporciones de errores configuradas, endpoints y descripción de su uso (aclaraciones adicionales).

### 2.4 Rúbrica

| Criterio | Ponderación |
| --- | ---: |
| Configuración funcional del stack ELK | 25% |
| Integración con logs reales de la API del servicio | 25% |
| Heartbeat funcional y reflejado en el dashboard | 15% |
| Dashboard completo con métricas relevantes | 25% |
| Informe técnico con claridad y evidencias | 10% |

La Fase 3 vale 20 puntos netos según el PDF. Se exige demostrar un sistema operativo, no únicamente capturas o código sin ejecutar.

## 3. Aclaraciones adicionales del proyecto

### 3.1 Origen de los logs y vía elegida

La aclaración permite API propia o API simulada. **Decisión vigente del equipo (2026-11-09): API REAL en preproducción** (`https://api-preprod.cuponmania.com.gt`). Sus logs ECS están en CloudWatch, log group `/aws/lambda/cuponmania-api-preprod`, con los siete campos obligatorios, `cuponmania.catalog_id`, `cuponmania.component` y `http.request.id`; la referencia de campos está en el repositorio de la API, `docs/infrastructure/logging.md`. La decisión anterior (API simulada) se conserva como alternativa local: el código de `api/` sigue disponible.

La API simulada debe:

- Exponer al menos **un endpoint por cada uno de los ocho elementos del catálogo de la Fase 1**.
- Dar respuestas exitosas y errores **4xx y 5xx** en proporciones configurables y documentadas.
- Tener tiempos de respuesta variables.
- Escribir los siete campos de logs exigidos automáticamente desde su propio código por cada petición finalizada.

Los endpoints pueden simular el negocio con datos ficticios. No son endpoints de Jira ni deben efectuar compras, pagos, reembolsos o cambios de cuenta reales.

### 3.2 Generador de tráfico

Un script realizará continuamente peticiones HTTP auténticas contra los ocho endpoints. Debe entregarse con el proyecto. La documentación y el informe deben explicar los endpoints, la proporción de errores elegida, las latencias y el funcionamiento del script. El generador no fabricará logs de la API ni insertará directamente documentos en Elasticsearch.

### 3.3 Uso de inteligencia artificial y reparto de autoría

La aclaración escrita permite usar IA para construir **la API simulada y el generador de tráfico**, y reserva al equipo la configuración del stack ELK y Heartbeat, el diseño del dashboard y la interpretación de resultados.

**Ampliación vigente (aprobación verbal del catedrático, comunicada el 2026-11-09):** el asistente también puede construir el `docker-compose.yml`, `filebeat.yml`, `heartbeat.yml`, la configuración de Elasticsearch y Kibana, las visualizaciones y el dashboard, y redactar el análisis del informe. Ver `docs/sources/aclaraciones-fase-3.md`, sección *Ampliación del uso de IA*.

Por tanto:

- Toda pieza hecha con IA se declara en `docs/uso-de-ia.md` y en el apartado final del informe.
- No se redactan resultados de observaciones que no existan ni se inventan datos o capturas.
- El equipo ejecuta, revisa y debe poder explicar cada configuración entregada.
- No usar ninguna skill de UI para este proyecto: **no hay interfaz propia que desarrollar**; la interfaz es Kibana.

## 4. Continuidad con Fases 1 y 2

### 4.1 Servicio y roles

CupónManía permite a comercios afiliados publicar promociones, a consumidores comprar cupones digitales y a personal autorizado validar/canjear códigos QR. El cliente principal es el comercio afiliado; los usuarios son consumidores y personal del comercio. La mesa de servicio se planteó como virtual, con atención regular de 07:00 a 22:00 (Guatemala) y guardia P1 24x7. En la Fase 1 se definieron niveles N1, N2 y N3 para el soporte y escalamiento.

### 4.2 Catálogo de ocho elementos y componentes de Jira

| ID de simulación (propuesto) | Elemento del catálogo | Tipo | Componente de Fase 2 |
| --- | --- | --- | --- |
| INC-01 | Compra de cupón no disponible | Incidente | Compras y pagos |
| INC-02 | Pago confirmado pero QR no generado | Incidente | QR y canje |
| INC-03 | QR válido no puede ser canjeado | Incidente | QR y canje |
| INC-04 | Plataforma indisponible o con degradación severa | Incidente | Plataforma |
| SR-01 | Alta o modificación de comercio | Solicitud de servicio | Comercios |
| SR-02 | Publicación o modificación de cupón | Solicitud de servicio | Promociones |
| SR-03 | Restablecimiento o desbloqueo de cuenta | Solicitud de servicio | Cuentas y accesos |
| SR-04 | Reembolso o cancelación según política | Solicitud de servicio | Reembolsos |

Los siete componentes pertenecen a la clasificación funcional de tickets, no son necesariamente siete microservicios. Una única API simulada puede utilizar `service.name = cuponmania-api` y guardar el componente en `cuponmania.component`. Los IDs INC/SR son una convención propuesta para identificar el origen funcional de los eventos; no sustituyen tickets CPM reales.

### 4.3 Matriz de priorización definida en Fase 1

| Impacto / Urgencia | Alta | Media | Baja |
| --- | --- | --- | --- |
| Alto | P1 - Crítica | P2 - Alta | P3 - Media |
| Medio | P2 - Alta | P3 - Media | P4 - Baja |
| Bajo | P3 - Media | P4 - Baja | P4 - Baja |

Los objetivos originales fueron: P1 respuesta 15 minutos / resolución 2 horas; P2 30 minutos / 4 horas; P3 4 horas / 1 día hábil; P4 8 horas / 3 días hábiles. Son objetivos de diseño, **no métricas históricas probadas** por la simulación.

La Fase 2 implementó Jira Service Management, espacio `CupónManía - Service Desk` con clave `CPM`, portal `Soporte CupónManía`, ocho formularios, siete componentes, seis colas, automatización de impacto/urgencia y dashboard de tickets. Estos artefactos **no sustituyen** la instrumentación y el dashboard de Kibana. No se requiere recrear Jira ni generar tickets Jira automáticamente con cada petición de la API.

## 5. Decisiones técnicas propuestas para la API SIMULADA (no exigidas literalmente)

### 5.1 Tecnología y endpoints de negocio

Propuesta: Python **FastAPI** para la API, **httpx** para el generador y **pytest** para las pruebas. Crear un Dockerfile para API y opcionalmente otro para el generador, sin generar configuración del stack ELK.

| Elemento | HTTP sugerido | Descripción |
| --- | --- | --- |
| INC-01 | `POST /api/v1/purchases` | Simular compra de cupón |
| INC-02 | `POST /api/v1/coupons/issue` | Simular emisión de QR tras pago |
| INC-03 | `POST /api/v1/coupons/redeem` | Simular canje QR |
| INC-04 | `GET /api/v1/platform/status` | Consultar estado de la plataforma |
| SR-01 | `POST /api/v1/merchants` | Solicitar alta/cambio de comercio ficticio |
| SR-02 | `POST /api/v1/promotions` | Solicitar publicar/modificar promoción ficticia |
| SR-03 | `POST /api/v1/accounts/recovery` | Solicitar desbloqueo de cuenta ficticia |
| SR-04 | `POST /api/v1/refunds` | Solicitar reembolso/cancelación ficticia |

Añadir `GET /healthz` para Heartbeat y salud del proceso (no sustituye los ocho endpoints). Mantener todas las rutas expuestas en la documentación OpenAPI de FastAPI si resulta práctico.

### 5.2 Errores y tiempos simulados

Propuesta inicial documentable por el equipo: perfil normal **90% 2xx, 5% 4xx, 5% 5xx**, con latencias variables de **80 a 350 ms**. Permitir cambiar porcentajes y tiempos sin editar código. Opcionalmente, un perfil de degradación QR con más 5xx y mayor latencia para hacer una prueba controlada.

Las proporciones son probabilidades configuradas: en muestras pequeñas, las proporciones observadas pueden ser diferentes. No ajustar artificialmente los registros para que coincidan. Utilizar datos falsos y no compartir secretos, tarjetas, tokens o contraseñas.

### 5.3 Formato de logs

Emitir **una línea JSON por petición** en un archivo `.log` accesible para la recolección que configurará el equipo. Campos mínimos:

| Campo | Requisito propuesto de implementación |
| --- | --- |
| `@timestamp` | UTC ISO 8601 con hora del evento |
| `http.request.method` | Método HTTP real |
| `http.response.status_code` | Código real devuelto, entero |
| `event.duration` | Tiempo real de servicio medido con reloj monotónico, **nanosegundos** según ECS |
| `url.path` | Ruta HTTP sin secretos de parámetros |
| `service.name` | `cuponmania-api` |
| `log.level` | INFO éxito, WARN 4xx, ERROR 5xx; convención propuesta |

Proponer además `event.id`, `cuponmania.catalog_id`, `cuponmania.component`, `cuponmania.scenario`, `cuponmania.synthetic` y `http.request.id`. Mantener estos campos adicionales como *propios del equipo*, no campos obligatorios del PDF. Asegurar tipos utilizables en Kibana y evitar que el log se duplique por middleware/excepciones.

**Atención a la unidad:** Kibana puede presentar `event.duration` en milisegundos mediante la conversión `nanosegundos / 1,000,000`; no interpretar el entero original como milisegundos.

### 5.4 Generador HTTP

El generador realizará peticiones reales a los ocho endpoints con velocidad moderada y configurable, concurrencia limitada, timeouts, escenario y duración/cantidad de peticiones. Debe funcionar indefinidamente hasta detenerlo, terminar correctamente bajo Ctrl+C y seguir operando ante errores 4xx, 5xx o caídas temporales.

Permitir una semilla y un modo secuencial determinista para pruebas reproducibles. La URL predeterminada debe ser local. No generar tráfico contra terceros. El generador registrará un resumen propio y no escribirá los logs del servidor ni documentos de Elasticsearch.

### 5.5 Pruebas y límites de lo que se puede afirmar

Probar: ocho rutas, tipos de respuesta, validación del perfil probabilístico, variación de tiempos, esquema JSON con siete campos, duración, códigos correctos, componente/ID correcto, apagado del generador, manejo de fallas y cobertura de todos los endpoints.

Para la muestra exigida, **ejecutar realmente** API y generador hasta registrar al menos 50 eventos `.log`; proporcionar instrucciones repetibles, no datos inventados. El equipo verificará por separado la llegada a Elasticsearch, Heartbeat y el dashboard.

## 6. Trabajo del equipo (configuración ELK y Kibana)

El equipo construirá `docker-compose.yml` y los archivos de recolección, Heartbeat y configuración necesarios, probará redes/volúmenes/permisos y la persistencia de datos. Se recomienda fijar la misma versión del stack para Elasticsearch, Kibana, Filebeat y Heartbeat; mantener contraseñas en variables locales fuera del repositorio y evitar exponer servicios en Internet.

El equipo decidirá y documentará la definición del error rate (por ejemplo, solo 5xx o 4xx+5xx), el denominador apropiado y la exclusión de `/healthz` del tráfico de negocio. Debe comprobar que `monitor.status` proviene de Heartbeat y que la disponibilidad del proceso no demuestra que una compra/canje se complete correctamente.

**Guía de navegación de Kibana para estudiantes:** `docs/pasos-kibana-equipo.md`. No contiene archivos de configuración listos, paneles creados automáticamente, datos inventados ni interpretación de resultados.

Para evidencias, capturar logs de 50+ registros, ingestión real, estado up/down de Heartbeat y dashboard con sus seis métricas. Elaborar interpretación propia y el informe técnico final con apartado de uso de IA.

## 7. Subagentes y archivos autorizados

El coordinador lee estos documentos y define el contrato de ocho endpoints/logs en `docs/contracts.md`.

| Agente | Responsabilidad | Archivos que puede modificar |
| --- | --- | --- |
| `api_builder` | API simulada, logs y Dockerfile de API | `api/`, `docs/api.md` |
| `traffic_builder` | Generador de tráfico y sus pruebas | `traffic/`, `docs/traffic.md` |
| `api_qa` | Pruebas integradas de API y generador | `tests/integration/`, `docs/qa-api-traffic.md` |

El coordinador puede editar contratos y documentación técnica de API/generador, pero no la infraestructura y dashboard reservados al equipo. Dividir responsabilidades antes de trabajar en paralelo para evitar conflictos. No afirmar subagentes usados si no estaban disponibles.

## 8. Lista de aceptación (pendiente de ejecución)

- [ ] API simulada con ocho endpoints funcionales y escenarios documentados.
- [ ] Script continuo de peticiones HTTP entregado y probado.
- [ ] Logs JSON producidos por el código con los siete campos mínimos; muestra real de 50+ eventos.
- [ ] Dockerfiles de API/generador si corresponde, creados y probados.
- [ ] `docker-compose.yml` del equipo con Elasticsearch, Kibana, Filebeat y Heartbeat; si se incluyen API/generador, deben estar conectados al mismo entorno.
- [ ] Recolección real de logs de API hasta Elasticsearch verificada.
- [ ] `heartbeat.yml` del equipo funcional y evidencias de disponibilidad.
- [ ] Dashboard construido por el equipo en Kibana con **seis** visualizaciones y captura completa.
- [ ] Informe de arquitectura, configuración, resultados, endpoints, proporciones, generador y evidencia.
- [ ] Apartado final de uso de IA honesto.

## 9. Referencias técnicas de consulta

- Guía oficial Elastic Docker: https://www.elastic.co/docs/deploy-manage/deploy/self-managed/install-kibana-with-docker
- Kibana Data Views: https://www.elastic.co/docs/explore-analyze/find-and-organize/data-views/create-data-view
- Kibana dashboards: https://www.elastic.co/docs/explore-analyze/dashboards/create-dashboard
- Kibana Lens: https://www.elastic.co/docs/explore-analyze/visualize/lens
- Heartbeat Docker: https://www.elastic.co/docs/reference/beats/heartbeat/running-on-docker
- ECS event.duration: https://www.elastic.co/docs/reference/ecs/ecs-event
- Codex subagentes: https://learn.chatgpt.com/docs/agent-configuration/subagents
