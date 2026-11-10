# Stack de observabilidad (Fase 3)

Elasticsearch, Kibana, Filebeat y Heartbeat 9.5.5 en Docker Compose, sobre la máquina de quien lo ejecuta (sin costo en AWS).

```text
API real (AWS Lambda, preprod) ──stdout ECS──► CloudWatch Logs /aws/lambda/cuponmania-api-preprod
                                                        │ (perfil AWS de solo lectura)
                                                        ▼
                         Filebeat (aws-cloudwatch) ──► Elasticsearch ◄── Heartbeat (HTTP)
                                                        │                  ├─ API preprod /health, /health/ready, catálogo
                                                        ▼                  └─ API simulada local /healthz
                                                     Kibana: dashboard «CupónManía | Salud de la API»
```

| Archivo | Contenido |
| --- | --- |
| `docker-compose.yml` | Los cuatro servicios exigidos, la API simulada (para la prueba de caída controlada) y `kibana-setup`, que importa los objetos de Kibana |
| `elk/filebeat/filebeat.yml` | Entrada `aws-cloudwatch`; decodifica el JSON ECS de cada línea y descarta las líneas de plataforma de Lambda |
| `elk/heartbeat/heartbeat.yml` | Cuatro monitores HTTP |
| `elk/kibana/saved-objects.ndjson` | Data views (con campos calculados), 8 visualizaciones Lens y el dashboard |

## Requisitos

- Docker con Compose v2 y unos 3 GB de RAM libres.
- Acceso de lectura a los logs: usuario de IAM Identity Center en el grupo `Equipo-CC3047` (permiso `LecturaLogsPreprod`) y un perfil de AWS CLI:

```bash
aws configure sso
#   SSO start URL: https://cuponmania.awsapps.com/start
#   SSO region: us-east-1
#   cuenta: cuponmania-preprod · rol: LecturaLogsPreprod
#   nombre del perfil: cuponmania-preprod
aws sso login --profile cuponmania-preprod      # la sesión dura 8 h; repetir al expirar
```

## Uso

```bash
cp .env.example .env               # ajustar AWS_PROFILE si el perfil tiene otro nombre
docker compose config -q           # valida el compose
docker compose up -d
docker compose ps                  # kibana-setup termina con código 0 tras importar el dashboard
docker compose logs --tail=50 filebeat
```

- Kibana: http://localhost:5601 → Dashboards → **CupónManía | Salud de la API**.
- Tráfico hacia la API real: `.venv/bin/python -m traffic.main --target real --rate 1 --concurrency 1 --duration 300` (ver `docs/traffic.md`).
- Prueba controlada de caída y recuperación de Heartbeat: `docker compose stop api-simulada`, esperar al menos 30 s, `docker compose start api-simulada`. El monitor «API simulada local · /healthz» pasa a down y vuelve a up. La API real no se apaga para esta prueba.
- Detener sin borrar datos: `docker compose stop`. `docker compose down -v` **borra** los datos de Elasticsearch.

## Definiciones del dashboard

- **Tráfico de negocio:** eventos de acceso (`event.kind: event`) de `cuponmania-api`, sin las rutas de salud (`cuponmania.catalog_id: INC-04`, que son `/health` y `/health/ready`; las consulta Heartbeat).
- **Tiempo de respuesta:** promedio de `event.duration` (nanosegundos), mostrado en milisegundos.
- **Error rate:** proporción de peticiones de negocio con código 5xx (falla del servicio). Los 4xx (error del cliente: sin sesión, datos inválidos) se grafican aparte y no cuentan como error del servicio.
- **Top endpoints:** método + plantilla de ruta (`http.route`), para que las rutas con identificadores no se dispersen; una petición sin ruta conocida se muestra con su `url.path`.
- **Estado del sistema:** último `monitor.status` de cada monitor de Heartbeat y su historia up/down.

## Seguridad del laboratorio

La seguridad de Elastic está desactivada y los puertos se publican solo en `127.0.0.1`. Filebeat monta la carpeta de AWS CLI en solo lectura y usa credenciales temporales de lectura; no hay llaves de acceso en el repositorio.
