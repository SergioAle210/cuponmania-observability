# Cómo configurar Kibana - Guía de trabajo del equipo

Esta es una guía de navegación y verificación. **No sustituye el trabajo propio de configuración ELK, dashboard e interpretación exigido al equipo.** Utiliza la documentación oficial correspondiente a la versión instalada. Los menús pueden variar ligeramente entre versiones.

## Paso 1. Elegir versiones y levantar los contenedores

- Instalar y abrir Docker Desktop. Elegir una misma versión compatible para Elasticsearch, Kibana, Filebeat y Heartbeat.
- Elaborar personalmente `docker-compose.yml`. El PDF exige Elasticsearch, Kibana, Filebeat y Heartbeat. Agregar API y generador como servicios auxiliares si conviene.
- Elaborar la configuración Filebeat que lea las líneas JSON auténticas de la API y las envíe a Elasticsearch. Evitar mezclar accidentalmente logs de la API con los del generador.
- Elaborar `heartbeat.yml` con un monitor HTTP para el ambiente de la API, por ejemplo su ruta `/healthz`; recordar que salud del proceso no garantiza salud de cada operación de negocio.
- Preparar volúmenes/permisos/red común y credenciales locales. Evitar publicar puertos de administración a Internet.
- Verificar las configuraciones y levantar el entorno:

```bash
docker compose config
docker compose up -d
docker compose ps
docker compose logs --tail=80 kibana
docker compose logs --tail=80 filebeat
docker compose logs --tail=80 heartbeat
```

No ejecutar esos comandos antes de que el Compose exista y esté revisado. No usar `docker compose down -v` sin querer eliminar datos persistentes.

## Paso 2. Abrir Kibana

- Si Kibana tiene publicado el puerto 5601, abrir **http://localhost:5601**.
- Ingresar con la cuenta/credenciales de la instalación local. La primera instalación de Elastic puede solicitar vinculación o enrolamiento, según cómo se haya configurado la seguridad.
- Si Kibana no abre, revisar el estado y los logs de los contenedores. Confirmar que puede comunicarse con Elasticsearch.

## Paso 3. Comprobar que llegan eventos

- Poner la API en marcha y ejecutar el generador durante un período de prueba.
- En Kibana entrar a **Discover**. Si aún no hay data view, desde el selector de vistas elegir **Create data view**, o buscar **Data Views** en la búsqueda global / Stack Management.
- Dar un nombre descriptivo, por ejemplo **CupónManía - API Logs**. El patrón de índices debe coincidir con el destino elegido realmente en Elasticsearch (por ejemplo, `filebeat-*` si se usó esa convención). No asumir que los índices existen antes de ingerir logs.
- Seleccionar `@timestamp` como campo temporal y guardar.
- En Discover fijar un intervalo que incluya las peticiones recientes (por ejemplo, **Últimos 15 minutos** o **Última hora**). Revisar registros con los siete campos exigidos, y filtrar por `service.name` cuando se mezclen servicios.
- Si los eventos llegan como texto en `message` y no como campos tipados, revisar la decodificación JSON configurada por el equipo. Verificar que códigos y duraciones sean numéricos, y que `@timestamp` sea tipo fecha.

## Paso 4. Revisar Heartbeat

- Verificar que Heartbeat envíe documentos a Elasticsearch mientras la API está arriba.
- En Discover seleccionar o crear una vista de datos que apunte a los índices/eventos Heartbeat (por ejemplo, `heartbeat-*` si esa es la convención realmente configurada).
- Comprobar que `monitor.status` refleje up/down. Para validarlo, realizar una parada y recuperación controladas de la API; no cambiar el gráfico manualmente.
- Diferenciar un monitor HTTP de salud del proceso de la verificación de compras/canjes completas.

## Paso 5. Construir personalmente el dashboard

- Abrir **Dashboards** → **Create dashboard** → **Add** / **Create visualization** (Kibana Lens).
- Crear **seis visualizaciones propias** con los datos recibidos, escogiendo personalmente el tipo de gráfico adecuado, títulos y colores. Requisitos que debe cumplir cada visualización:

| Visualización obligatoria | Qué debe representar |
| --- | --- |
| Tráfico de peticiones | Conteo de peticiones de API por intervalo, sobre `@timestamp` |
| Tiempo de respuesta promedio | Promedio de duración real de la API, con unidad correcta; si `event.duration` está en ns, convertir a ms dividiendo entre 1,000,000 |
| Estado del sistema (up/down) | Estado comprobado por Heartbeat, no una etiqueta inventada |
| Distribución por códigos HTTP | Conteo o distribución de `http.response.status_code` |
| Error rate | Proporción de errores sobre peticiones elegibles, con criterio explícito para 4xx/5xx |
| Top endpoints | Rutas más solicitadas según `url.path` |

- Filtrar peticiones de negocio para no contar `/healthz` como tráfico de clientes. Decidir y documentar si los errores 4xx se incluyen en la tasa de error. Mantener las fuentes de Heartbeat y API claramente diferenciadas.
- Guardar el dashboard con un nombre claro, por ejemplo **CupónManía | Salud de API**.
- Capturar el dashboard completo, sus seis visualizaciones y la evidencia de logs/Heartbeat. El diseño y la interpretación son del equipo.

## Paso 6. Elaborar evidencias e informe

- Entregar `docker-compose.yml`, archivo `.log` con mínimo 50 registros genuinos, `heartbeat.yml`, captura del dashboard y el informe técnico.
- El informe debe explicar arquitectura, versión, componentes, flujo de ingesta, API simulada y sus ocho endpoints, proporciones de respuesta, generador, disponibilidad, resultados realmente obtenidos y declaración final del uso de IA.
- No afirmar SLA mensual, disponibilidad 99.9% o tiempos p95 como hechos de producción: el laboratorio es una simulación.

## Documentación oficial de apoyo

- Docker/Kibana: https://www.elastic.co/docs/deploy-manage/deploy/self-managed/install-kibana-with-docker
- Crear data view: https://www.elastic.co/docs/explore-analyze/find-and-organize/data-views/create-data-view
- Dashboards: https://www.elastic.co/docs/explore-analyze/dashboards/create-dashboard
- Lens: https://www.elastic.co/docs/explore-analyze/visualize/lens
- Heartbeat: https://www.elastic.co/docs/reference/beats/heartbeat/running-on-docker
