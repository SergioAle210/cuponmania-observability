# Stack de observabilidad (Fase 3)

Elasticsearch, Kibana, Filebeat y Heartbeat 9.5.5 en Docker Compose, sobre la máquina de quien lo ejecuta (sin costo en AWS).

**Integración del 16 de noviembre de 2026:** se incorporaron los cambios del equipo: nueve paneles y 12 objetos, p95 de latencia, exclusión de `OPTIONS`, error rate por hora, latencia de Heartbeat, página de inicio del dashboard y reinicio automático de Elasticsearch/Kibana. `kibana-setup` vuelve a `curlimages/curl:8.11.1`; no necesita una imagen Python. Las comprobaciones del párrafo siguiente corresponden a la versión anterior de ocho paneles. Docker estaba apagado durante esta integración: queda pendiente ejecutar aquí el importador curl y revisar los nueve paneles actualizados.

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
| `elk/kibana/saved-objects.ndjson` | Data views (con campos calculados), 9 visualizaciones Lens y el dashboard |

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

`kibana-setup` usa el script curl del equipo, importa los objetos y configura `defaultRoute`. Revisar en su salida `success: true`, `successCount: 12`, los doce identificadores y ausencia de errores. **Un código de salida 0 o un HTTP 200 no garantizan una importación completa:** curl detecta errores HTTP y de transporte, pero no valida el contenido JSON. `.gitattributes` conserva finales LF compatibles con Linux y con un checkout Windows.

Para una importación con validación JSON automática, se conserva como opción local el programa Python ya probado; Compose no lo ejecuta ni descarga una imagen Python para el setup. Con el entorno de desarrollo existente y Kibana activo:

```powershell
.venv/Scripts/python.exe elk/kibana/import_objects.py --url http://localhost:5601
```

En Linux/macOS, usar `.venv/bin/python` en ese comando. La utilidad vuelve a importar con `overwrite=true` y comprueba todos los identificadores presentes en `saved-objects.ndjson`, sin una cantidad fija. No cambia `defaultRoute`; ese ajuste lo realiza `import.sh`. Los 12 objetos actuales son dos data views, nueve visualizaciones y un dashboard.

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

- Kibana: http://localhost:5601 abre directamente el dashboard **CupónManía | Salud de la API** (`kibana-setup` lo deja como página de inicio con el ajuste `defaultRoute`). También está en Dashboards.
- La página «Elasticsearch» del menú de Kibana (inicio de búsqueda) muestra un error: consulta la API de seguridad para ofrecer API keys, y la seguridad de Elastic está desactivada en este laboratorio. No afecta al dashboard ni a la ingesta; el log de Kibana lo registra como `no handler found for uri [/_security/user/_has_privileges]`.
- Tráfico hacia la API real: `.venv/bin/python -m traffic.main --target real --rate 1 --concurrency 1 --duration 300` (ver `docs/traffic.md`).
- Prueba controlada de caída y recuperación de Heartbeat: `docker compose stop api-simulada`, esperar 45 s, `docker compose start api-simulada`. Comprobar que el monitor «API simulada local · /healthz» pasa a down y vuelve a up. La API real no se apaga para esta prueba.
- Detener sin borrar datos: `docker compose stop`. `docker compose down -v` **borra** los datos de Elasticsearch.
- Elasticsearch y Kibana tienen `restart: unless-stopped`, igual que los Beats: tras reiniciar Docker o el equipo vuelven todos. Antes solo volvían los Beats y Filebeat/Heartbeat quedaban sin destino.

## Credenciales de AWS (IAM Identity Center)

Filebeat monta `~/.aws` en **solo lectura**. El SDK dentro del contenedor usa el token de IAM Identity Center guardado en `~/.aws/sso/cache`, pero no puede escribir uno renovado. Por eso:

- Ejecutar `aws sso login --profile cuponmania-preprod` **justo antes** de `docker compose up` (o de reiniciar Filebeat).
- Si `docker compose logs filebeat` muestra `refresh cached SSO token failed ... read-only file system`, el token expiró: repetir `aws sso login` en el equipo y luego `docker compose restart filebeat`. Mientras tanto no se pierden eventos: siguen en CloudWatch (14 días) y se pueden recuperar como indica la sección siguiente.
- Que la CLI siga funcionando en el equipo no basta: la CLI usa su propia caché de credenciales (`~/.aws/cli/cache`), que Filebeat no lee.

## Recuperar un hueco de eventos

Si Filebeat estuvo corriendo sin Elasticsearch, o sin credenciales válidas, su registro puede haber avanzado sin indexar esos eventos. Cada documento usa como `_id` el identificador del evento de CloudWatch, así que releer es idempotente: los repetidos se rechazan (409) y no se duplican. Con el stack arriba y la sesión de AWS recién iniciada:

```bash
docker compose run -d --rm --no-deps --name filebeat-relectura filebeat \
  filebeat -e --strict.perms=false --path.data /tmp/relectura
# esperar a que el conteo de filebeat-* deje de crecer y detenerla:
docker stop filebeat-relectura
```

Usa un registro temporal (`/tmp/relectura` dentro del contenedor) y vuelve a leer los 14 días retenidos sin tocar el registro del Filebeat principal.

## Verificación del 2026-11-13

Observado de verdad sobre CloudWatch y el stack local (hora UTC), después de los despliegues del 2026-11-12 de la API:

- **Formato de los logs:** la línea de acceso por petición conserva los siete campos exigidos y los de apoyo (`http.route`, `http.request.id`, `cuponmania.catalog_id`, `cuponmania.component`) con los mismos tipos (`event.duration` entero en ns, `http.response.status_code` numérico). Las rutas con códigos secretos se registran redactadas (`/api/v1/redemptions/[REDACTED]`). La API agrega líneas de aplicación sin `event.kind` (por ejemplo `Server started`, `Unhandled error`) con datos en `cuponmania.context.*`; Filebeat las indexa y el dashboard no las cuenta, porque todas las visualizaciones filtran `event.kind : event`. No hizo falta cambiar `filebeat.yml` ni los objetos de Kibana.
- **Heartbeat:** `/health` (`{"status":"ok","db":"ok"}`), `/health/ready` y el catálogo responden 200 por `api-preprod.cuponmania.com.gt` (Cloudflare). La concurrencia reservada de la Lambda sigue en 1, así que los monitores siguen escalonados. Las llamadas directas a la URL de Lambda reciben 403 (bloqueo de origen); en CloudWatch aparecen como `GET /health 403` con duración 0 y no vienen de Heartbeat.
- **Falla encontrada y corregida:** Elasticsearch y Kibana llevaban unas 37 h detenidos tras un reinicio, mientras Filebeat y Heartbeat seguían corriendo sin destino. Faltaban en el índice los eventos del 2026-11-11 y del 2026-11-12. Tras agregar la política de reinicio y hacer la relectura: 1694 eventos de acceso del 2026-11-11 y 296 del 2026-11-12, la misma cifra que da CloudWatch para esos días. La ventana del informe (2026-11-10 15:47:53–16:07:52) sigue dando 1274 eventos.
- **Extremo a extremo:** Filebeat indexó eventos de hasta 05:04 UTC sin errores de mapeo, los cuatro monitores quedaron *up* y los ocho paneles del dashboard mostraron datos. Entre 00:00 y 05:05 UTC del 2026-11-13 hubo 299 peticiones de negocio (sin las de salud): 274 2xx, 12 4xx y 13 5xx (error rate 5xx 4.3 %). Los 13 5xx (11 de 503 y 2 de 500) están todos en rutas del backoffice (`/api/v1/businesses`, `/users`, `/roles` y cuentas bancarias), no en las que usa el generador. Estas cifras son una observación nueva y **no** sustituyen a las del informe.

## Verificación del 2026-11-16

Stack levantado desde cero en un proyecto de compose aparte (volúmenes nuevos, sin puertos publicados), con el perfil de AWS de solo lectura (`LecturaLogsPreprod`), y luego borrado:

- `kibana-setup` importó los 11 objetos y dejó el dashboard como página de inicio; `GET /` redirige a la entrada de espacios, que abre el dashboard.
- Filebeat indexó más de 4700 eventos de CloudWatch sin líneas de error.
- Heartbeat: los cuatro monitores *up*. Prueba de caída controlada: con `api-simulada` detenida el monitor «API simulada local · /healthz» pasó a *down* en 30 s y volvió a *up* 15 s después de arrancarla.
- Generador contra la API real (`--target real --rate 1 --concurrency 1 --duration 30`): 22 peticiones; las líneas de esa ventana en CloudWatch y en `filebeat-*` coinciden (mismas rutas y códigos).
- `pytest`: 141 aprobadas.
- En el stack de trabajo, la relectura de 14 días no agregó eventos: no había hueco.

Cambio en la API desde la verificación anterior: desde el 2026-11-15 la Lambda de la API tiene concurrencia reservada de 5 (antes 1) y los límites de tasa se guardan en PostgreSQL. Las cifras y conclusiones del informe corresponden a la configuración anterior y no se modificaron.

## Definiciones del dashboard

- **Tráfico de negocio:** eventos de acceso (`event.kind: event`) de `cuponmania-api`, sin las rutas de salud (`cuponmania.catalog_id: INC-04`, que son `/health` y `/health/ready`; las consulta Heartbeat) y sin las peticiones `OPTIONS`. Las `OPTIONS` son preflights de CORS que hace el navegador antes de llamar a la API: siempre responden 204, no son peticiones de negocio y, si se cuentan, inflan el tráfico y bajan el error rate. Este criterio aplica a los seis paneles de la API.
- **Tiempo de respuesta:** promedio y percentil 95 de `event.duration` (nanosegundos), mostrados en milisegundos. El promedio esconde las peticiones lentas; el p95 es el tiempo que no supera el 95 % de las peticiones.
- **Error rate:** proporción de peticiones de negocio con código 5xx (falla del servicio). Los 4xx (error del cliente: sin sesión, datos inválidos) se grafican aparte y no cuentan como error del servicio. La gráfica agrupa por hora: con intervalos cortos y poco tráfico, una sola respuesta de error se veía como 100 %. Aun por hora, una hora con muy pocas peticiones puede mostrar un porcentaje alto; conviene leerla junto al panel de tráfico.
- **Top endpoints:** método + plantilla de ruta (`http.route`), para que las rutas con identificadores no se dispersen; una petición sin ruta conocida se muestra con su `url.path`.
- **Estado del sistema:** último `monitor.status` de cada monitor de Heartbeat y su historia up/down.
- **Tiempo de respuesta de los monitores:** promedio de `monitor.duration.us` de cada monitor de Heartbeat, en milisegundos. Complementa el estado up/down con la rapidez con que responde cada objetivo.

## Seguridad del laboratorio

La seguridad de Elastic está desactivada y los puertos se publican solo en `127.0.0.1`. Filebeat monta la carpeta de AWS CLI en solo lectura y usa credenciales temporales de lectura; no hay llaves de acceso en el repositorio.
