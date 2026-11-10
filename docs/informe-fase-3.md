# Informe técnico — Fase 3: monitoreo de CupónManía con ELK

> **Borrador para revisión del equipo.** Las cifras salen de una ejecución real del 2026-11-10 (ventana 15:47:53–16:07:53 UTC; 09:47–10:07 hora de Guatemala) y de las consultas a Elasticsearch descritas en cada sección. El equipo debe revisarlo, completarlo y poder explicar cada parte antes de entregarlo.

## 1. Vía elegida y arquitectura

El equipo eligió la **API real de CupónManía en preproducción** (`https://api-preprod.cuponmania.com.gt`) como fuente de los logs. La API simulada del repositorio se conserva como alternativa local y se usa para la prueba controlada de caída de Heartbeat.

```text
Generador (traffic/) ──HTTPS──► Cloudflare ─► CloudFront ─► AWS Lambda (API, Bun)
                                                              │ una línea JSON ECS por petición
                                                              ▼
                                         CloudWatch Logs /aws/lambda/cuponmania-api-preprod
                                                              │ perfil AWS de solo lectura
                                                              ▼
                     Filebeat (aws-cloudwatch) ─────────► Elasticsearch ◄──── Heartbeat
                                                              │              (4 monitores HTTP)
                                                              ▼
                                         Kibana — dashboard «CupónManía | Salud de la API»
```

- **Stack:** Elasticsearch, Kibana, Filebeat y Heartbeat 9.5.5 en Docker Compose (`docker-compose.yml`), en la máquina del equipo. La guía de uso está en `docs/elk.md`.
- **Logs:** la API los escribe desde su propio código, una línea por petición terminada, en formato ECS 8.11. Incluyen los siete campos exigidos (`@timestamp`, `http.request.method`, `http.response.status_code`, `event.duration` en nanosegundos, `url.path`, `service.name`, `log.level`), además de `http.route`, `http.request.id` y el elemento del catálogo de la Fase 1 (`cuponmania.catalog_id`, `cuponmania.component`).
- **Filebeat:** entrada `aws-cloudwatch`. Decodifica el JSON de cada línea y descarta las líneas de plataforma de Lambda (START/END/REPORT). Usa la plantilla ECS de Filebeat, con lo que el código HTTP y la duración quedan numéricos y `@timestamp` como fecha.
- **Heartbeat:** cuatro monitores.
  - En la API real: `/health` (proceso y base de datos), `/health/ready` y el catálogo público de cupones.
  - En la API simulada local: `/healthz`.

## 2. Generador de tráfico y endpoints

`traffic/main.py --target real` recorre doce rutas: los ocho elementos del catálogo de la Fase 1 (INC-01 a INC-04, SR-01 a SR-04) y dos rutas públicas del catálogo de cupones.

- Envía las peticiones **sin sesión y con cuerpos vacíos**, de modo que no crea compras, canjes ni datos reales.
- Por eso los 4xx son el resultado esperado de la mayoría de rutas: la proporción de errores la determina la API real, no un parámetro del generador.
- Ejecución medida: `--rate 1 --concurrency 1 --duration 1200 --seed 42`.

| Resultado del generador (`evidencias/ejecucion-preprod.json`) | Valor |
| --- | ---: |
| Peticiones completadas | 1196 |
| 200 | 399 |
| 401 | 697 |
| 429 | 90 |
| 400 | 10 |
| Errores de transporte | 0 |

## 3. Evidencias

- `evidencias/api-preprod.log`: **1274 líneas** de acceso exportadas tal cual de CloudWatch para la ventana de la ejecución (generador y Heartbeat). El SHA-256 y el comando de exportación están en `evidencias/ejecucion-preprod.json`.
- `evidencias/capturas/dashboard-kibana.png`: el dashboard completo sobre la misma ventana.
- Objetos de Kibana reproducibles: `elk/kibana/saved-objects.ndjson`, que se importan solos al levantar el compose.

## 4. Resultados observados

Fuente: Elasticsearch, eventos de acceso de `cuponmania-api` entre 15:47:53 y 16:07:53 UTC.

**Tráfico de negocio**, que excluye `/health` y `/health/ready` (INC-04): **1015 peticiones**.

| Código | Peticiones | Proporción |
| --- | ---: | ---: |
| 401 | 697 | 68.7 % |
| 200 | 219 | 21.6 % |
| 429 | 89 | 8.8 % |
| 400 | 10 | 1.0 % |
| 5xx | 0 | 0 % |

**Tiempo de respuesta medido por la API** (`event.duration`, tráfico de negocio):

| Estadístico | Valor |
| --- | ---: |
| Promedio | 5.4 ms |
| Mediana | 3.0 ms |
| p95 | 10.5 ms |
| p99 | 19.6 ms |
| Máximo | 260.1 ms |

Por ruta:
- Las que rechazan por falta de sesión (401) responden en unos 3 ms.
- Las que consultan la base: catálogo de cupones 12.6 ms y categorías 10.8 ms en promedio.

**Salud:** 260 peticiones a `/health` y `/health/ready`, todas 200, con 2.1 ms de promedio dentro de la API.

**Heartbeat** (15:36–16:10 UTC):

| Monitor | up | down | Causa de los down | Tiempo medio del chequeo |
| --- | ---: | ---: | --- | ---: |
| API preprod · /health | 62 | 5 | 429, todos antes de las 15:47:42 | 368 ms |
| API preprod · /health/ready | 27 | 6 | 429, todos antes de las 15:47:42 | 405 ms |
| API preprod · catálogo | 27 | 6 | 429, todos antes de las 15:47:42 | 373 ms |
| API simulada · /healthz | 131 | 4 | sin respuesta (prueba de caída) | 3 ms |

## 5. Análisis

1. **El servicio no falló en el periodo medido.** El error rate (5xx sobre el tráfico de negocio) fue de **0 %**.
   - Los 4xx no cuentan como falla del servicio. Los 401 son el control de autenticación funcionando ante peticiones sin sesión. Los 400 son validación de datos.
   - Por eso el dashboard grafica 5xx y 4xx por separado.
2. **Los 429 del tráfico de negocio son un control de seguridad, no saturación.** Los 89 corresponden a `/api/v1/account-recovery/request`, cuyo límite es de 5 solicitudes por cada 15 minutos para evitar abuso de la recuperación de cuentas. El generador recibió 90 respuestas 429 y la API registró 89; la diferencia es compatible con un rechazo de Lambda por concurrencia que no llega a la API (punto 3).
3. **Heartbeat detectó un límite de capacidad real.** La API corre con concurrencia reservada de 1 instancia en Lambda. Cuando los monitores disparaban en el mismo segundo, Lambda rechazaba la petición simultánea con 429 antes de que llegara a la API.
   - La métrica `Throttles` de CloudWatch marcó 0 en los intervalos anteriores y 21 entre 15:15 y 15:45 UTC, cuando arrancó el monitoreo.
   - Al escalonar los monitores (15:47:42 UTC), los down desaparecieron: ningún down de preprod después de esa hora.
   - Para atender peticiones simultáneas de usuarios hace falta más de una instancia. Eso requiere antes mover la idempotencia y los límites de tasa a un almacén compartido. Se dejó como mejora posterior.
4. **La mayor parte de la latencia que percibe el cliente está fuera de la API.** Heartbeat mide unos 370–400 ms por chequeo desde Guatemala, mientras la API procesa `/health` en 2.1 ms. La diferencia corresponde a red, TLS y el paso por Cloudflare, CloudFront y la URL de la función. Es el margen a revisar si se quiere bajar la latencia percibida.
5. **La prueba controlada de caída funcionó.** Al detener la API simulada (15:48:00–15:49:10 UTC), Heartbeat registró 4 chequeos down y volvió a up al reiniciarla. Esto demuestra que el panel de estado refleja caídas reales.

## 6. Limitaciones

- La ventana es corta (20 minutos) y el tráfico es sintético y sin sesión: no ejercita compras, canjes ni pagos reales. Los percentiles no son un SLA de producción.
- El laboratorio corre con la seguridad de Elastic desactivada y puertos solo en `127.0.0.1`.

## 7. Uso de inteligencia artificial

Ver `docs/uso-de-ia.md`.

- La API simulada, el generador, la instrumentación de la API real y el stack ELK se construyeron con asistencia de IA. Lo mismo vale para el compose, Filebeat, Heartbeat, Kibana y el dashboard, bajo la ampliación aprobada en persona por el catedrático, registrada en `docs/sources/aclaraciones-fase-3.md`.
- Este borrador de análisis también se redactó con IA, a partir de las cifras observadas que se citan.
- El equipo revisa, ejecuta y debe poder explicar cada parte.
