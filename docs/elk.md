# Stack de observabilidad (Fase 3)

Elasticsearch, Kibana, Filebeat y Heartbeat 9.5.5 en Docker Compose, sobre la máquina de quien lo ejecuta (sin costo en AWS).

**Estado comprobado el 15 de noviembre de 2026, 23:55 Guatemala:** SSO e ingesta de CloudWatch funcionan. Pasaron la caída controlada de la API simulada, el reinicio de Filebeat y la persistencia tras recrear los cuatro contenedores de observabilidad con los mismos volúmenes. Una ventana fija de 8755 eventos conservó IDs, versiones y contenido; también se conservaron los 11 objetos de Kibana sin reimportarlos. La ingesta continuó y los ocho paneles muestran datos. Evidencias y alcance: `evidencias/2026-11-15-pruebas-stack/README.md`. Hay un par de mensajes idénticos que ya venía de CloudWatch antes del ensayo; no se añadieron duplicados durante las pruebas. Las comprobaciones anteriores se conservan en `evidencias/2026-11-15-validacion-local/`.

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
aws sso login --profile cuponmania-preprod      # repetir cuando expire la sesión
```

## Uso

### Windows / PowerShell

Desde la raíz del repositorio, localizar Docker instalado por usuario. Este ajuste de PATH dura solo en la terminal actual:

```powershell
$dockerExe = Join-Path $env:LOCALAPPDATA 'Programs/DockerDesktop/resources/bin/docker.exe'
$env:PATH = (Split-Path $dockerExe) + ';' + $env:PATH
& $dockerExe version
```

AWS CLI se ejecuta en un contenedor temporal, sin instalación global. La carpeta SSO queda fuera del repositorio. Configurar el perfil una vez y completar personalmente el enlace/código de AWS:

```powershell
$awsDirectory = Join-Path $env:USERPROFILE '.aws'
New-Item -ItemType Directory -Path $awsDirectory -Force | Out-Null
& $dockerExe run --rm -it --mount "type=bind,source=$awsDirectory,target=/root/.aws" public.ecr.aws/aws-cli/aws-cli:latest configure sso --profile cuponmania-preprod --no-browser --use-device-code
```

Elegir sesión `cuponmania`, URL `https://cuponmania.awsapps.com/start`, región SSO y región de servicios `us-east-1`, alcance `sso:account:access`, cuenta **cuponmania-preprod**, rol **LecturaLogsPreprod** y salida `json`. No copiar contraseñas ni tokens al proyecto. Para renovar la sesión, sin reconfigurar el perfil:

```powershell
& $dockerExe run --rm -it --mount "type=bind,source=$awsDirectory,target=/root/.aws" public.ecr.aws/aws-cli/aws-cli:latest sso login --profile cuponmania-preprod --no-browser --use-device-code
```

Si AWS indica contactar al administrador, el administrador del equipo debe revisar el acceso del usuario al portal, la cuenta y el permiso `LecturaLogsPreprod`. No se determinó la causa exacta del mensaje inicial; el usuario obtuvo acceso y **`configure sso` ya se completó en esta máquina**. `sso login` sirve para renovar ese perfil. Para iniciar Filebeat, usar `& $dockerExe compose up -d filebeat` y comprobar sus logs y la llegada de eventos a Elasticsearch.

Preparar `.env` solo si no existe. `AWS_CONFIG_DIR=~/.aws` se resuelve a la carpeta del usuario; también admite una ruta absoluta con `/`. Filebeat la monta en solo lectura:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
& $dockerExe compose config --quiet
& $dockerExe compose pull
& $dockerExe compose up -d --build
& $dockerExe compose ps -a
& $dockerExe compose logs --tail 30 kibana-setup
& $dockerExe compose logs --tail 50 filebeat
```

`kibana-setup` debe terminar con código 0 y confirmar `success: true`, `successCount: 11` y los once identificadores sin errores. Usa Python estándar y rechaza HTTP 200 con errores parciales. `.gitattributes` fija los scripts `.sh` a LF para Linux desde un checkout Windows.

Compartir el cambio del importador junto con `docker-compose.yml`, que ahora usa `python:3.13-slim` para `kibana-setup`. La validación corresponde a los 11 objetos del export actual; si el equipo agrega o elimina objetos en `saved-objects.ndjson`, debe actualizar también esa comprobación y sus pruebas.

Abrir [el dashboard](http://localhost:5601/app/dashboards#/view/cuponmania-salud-api). Para la muestra histórica seleccionar el 10 de noviembre de 2026, 15:47:53–16:07:53 **UTC** (09:47:53–10:07:53 Guatemala), **si esos eventos ya fueron ingeridos**; `Últimas 24 horas` no muestra esa muestra después del 11 de noviembre. El archivo `.log` conservado en el repositorio no se carga automáticamente al cambiar el selector de fechas. Para generar tráfico nuevo:

```powershell
.venv/Scripts/python.exe -m traffic.main --target real --rate 1 --concurrency 1 --duration 300 --seed 42
```

Filebeat consulta cada 30 segundos con un desfase de un minuto: esperar hasta dos minutos tras terminar el generador antes de cotejar registros. `start_position: lastSync` y el volumen `filebeatdata` conservan el avance; sin registro previo se comienza por el histórico. Comprobar IDs de petición de una ventana fija antes/después de reiniciar Filebeat para detectar duplicados.

Apagar conservando datos: `& $dockerExe compose stop`. Volver a arrancar: `& $dockerExe compose up -d`. No usar `down -v` para la demostración: borra los volúmenes. Si caduca SSO, renovar la sesión; si Filebeat sigue reportando credenciales vencidas, usar `& $dockerExe compose restart filebeat` y verificar la recuperación.

Para volver a iniciar los contenedores existentes después de `compose stop`: `& $dockerExe compose start elasticsearch kibana filebeat heartbeat api-simulada`. Elasticsearch puede mostrar salud de clúster `yellow` en este laboratorio de un nodo porque no puede asignar una réplica junto a su primario; la comprobación local confirmó esa causa, primarios activos y acceso a los datos de Heartbeat.

Antes de presentar, confirmar que Docker está activo y SSO vigente; renovar SSO con el comando anterior si expiró. Abrir el dashboard, elegir la ventana que se va a explicar y comprobar eventos recientes. Los ensayos verifican este equipo; el informe y la declaración de IA todavía deben ser revisados por el equipo. La persistencia probada corresponde a Elasticsearch, objetos de Kibana y registro de Filebeat: Compose no monta un volumen para el archivo de logs de la API simulada.

### Linux / macOS

```bash
cp .env.example .env               # ajustar AWS_PROFILE si el perfil tiene otro nombre
docker compose config -q           # valida el compose
docker compose up -d
docker compose ps                  # kibana-setup termina con código 0 tras importar el dashboard
docker compose logs --tail=50 filebeat
```

- Kibana: http://localhost:5601 → Dashboards → **CupónManía | Salud de la API**.
- Tráfico hacia la API real: `.venv/bin/python -m traffic.main --target real --rate 1 --concurrency 1 --duration 300` (ver `docs/traffic.md`).
- Prueba controlada de caída y recuperación de Heartbeat: `docker compose stop api-simulada`, esperar 45 s, `docker compose start api-simulada`. Comprobar que el monitor «API simulada local · /healthz» pasa a down y vuelve a up. La API real no se apaga para esta prueba.
- Detener sin borrar datos: `docker compose stop`. `docker compose down -v` **borra** los datos de Elasticsearch.

## Definiciones del dashboard

- **Tráfico de negocio:** eventos de acceso (`event.kind: event`) de `cuponmania-api`, sin las rutas de salud (`cuponmania.catalog_id: INC-04`, que son `/health` y `/health/ready`; las consulta Heartbeat).
- **Tiempo de respuesta:** promedio de `event.duration` (nanosegundos), mostrado en milisegundos.
- **Error rate:** proporción de peticiones de negocio con código 5xx (falla del servicio). Los 4xx (error del cliente: sin sesión, datos inválidos) se grafican aparte y no cuentan como error del servicio.
- **Top endpoints:** método + plantilla de ruta (`http.route`), para que las rutas con identificadores no se dispersen; una petición sin ruta conocida se muestra con su `url.path`.
- **Estado del sistema:** último `monitor.status` de cada monitor de Heartbeat y su historia up/down.

## Seguridad del laboratorio

La seguridad de Elastic está desactivada y los puertos se publican solo en `127.0.0.1`. Filebeat monta la carpeta de AWS CLI en solo lectura y usa credenciales temporales de lectura; no hay llaves de acceso en el repositorio.
