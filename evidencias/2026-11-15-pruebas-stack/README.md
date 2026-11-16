# Pruebas finales del stack — 15 de noviembre de 2026

Ejecutadas en esta computadora entre 23:47 y 23:55 de Guatemala (16 de noviembre, 05:47–05:55 UTC). Los JSON conservan fechas precisas, consultas y comandos realmente usados; los `.json.gz` contienen proyecciones auténticas de documentos de Elasticsearch, no logs fabricados. Las muestras `.log` y la captura histórica del repositorio no se modificaron.

| Verificación | Resultado | Evidencia |
| --- | --- | --- |
| Caída de API simulada | Espera monotónica de 45.0003812 s después de detenerla; up/down/up, tres down; seis chequeos de preproducción up | `02-caida.json` |
| Reinicio de Filebeat | 8755 documentos antes/después, mismos IDs, campos exportados y versiones; evento nuevo posterior al reinicio | `03-antes-reinicio-filebeat.*`, `04-despues-reinicio-filebeat.*`, `05-reinicio-filebeat.json` |
| Persistencia | Nuevos contenedores ES/Kibana/Filebeat/Heartbeat, mismos volúmenes ES/Filebeat, 8755 documentos y 11 objetos conservados; no se ejecutó importación | `06-antes-persistencia.*`, `07-despues-persistencia.*`, `08-persistencia.json` |
| Comparación posterior al avance de ingesta | Mismo hash y versiones después de observar eventos nuevos, sin duplicados ni reescrituras añadidos en la ventana | `11-despues-de-reanudar-ingesta.*`, `12-comparacion-final.json` |
| Estado final | ES/Kibana saludables; Filebeat, Heartbeat y API activos; cuatro monitores up; 8864 accesos totales, 53 en los últimos cinco minutos, siete campos presentes | `10-estado-final.json` |

## Ventana y duplicados

Ventana cerrada: `2026-11-10T00:00:00Z <= @timestamp < 2026-11-16T05:42:44.477401+00:00`, con `event.kind:event` y `service.name:cuponmania-api`. Se exportaron todos sus documentos mediante scroll, con total exacto y proyección declarada en cada JSON. Los datos se ordenaron por `(_index, _id)` antes de calcular el hash; este incluye `_version`, `event.ingested` y los campos exportados. El hash SHA-256 canónico fue idéntico en todas las comparaciones:

`93cd47507f0cbd4126dd2a8351cfd967f1bb7b4e1481dfaa6f49e3fc9ad98be8`

Ya había 8735 request IDs distintos en 8755 documentos antes del ensayo. Diecinueve pares con ID compartido tienen datos distintos; un par tiene mensajes idénticos y dos eventos distintos en CloudWatch, confirmados directamente en `09-id-repetido-origen.json`. No se borró ni alteró ningún evento. **El ensayo no añadió duplicados a esta ventana; no afirma que el origen carezca de duplicados.**

## Operaciones realizadas

Desde la raíz del proyecto, con Docker disponible en PATH:

```powershell
docker compose stop api-simulada
# Espera real de 45 segundos después de finalizar la parada; arranque protegido con finally.
docker compose start api-simulada
docker compose restart filebeat
# Esperar un evento con timestamp posterior al reinicio y volver a comparar la ventana fija.
docker compose stop filebeat heartbeat kibana
# Tomar snapshot antes de detener Elasticsearch.
docker compose stop elasticsearch
docker compose up -d --force-recreate elasticsearch kibana filebeat heartbeat
# Esperar salud, comparar documentos/objetos y observar ingesta posterior.
```

Los comandos no se ejecutaron seguidos sin comprobaciones: los documentos guardan el orden, la espera de recuperación de Heartbeat, eventos nuevos después de cada reinicio, IDs de contenedor y nombres de volúmenes antes/después. No se borraron volúmenes ni se ejecutó `kibana-setup` durante el ensayo. La API real permaneció intacta. La persistencia comprobada es la de Elasticsearch, objetos de Kibana y registro de Filebeat; no hay un volumen de logs de la API simulada en este Compose.

## Capturas y límites

`dashboard-superior.jpg` y `dashboard-inferior.jpg` son dos vistas complementarias del dashboard después de recrear los contenedores, con el selector **Last 24 hours**. Se observaron los ocho paneles con datos, latencia en milisegundos y cuatro monitores up. Sus cifras usan otra ventana que los 8755 documentos de comparación; no son una nueva ejecución del generador. La captura histórica completa sigue en `../capturas/dashboard-kibana.png`.

`error-prepare.json` registra el primer intento del comprobador, rechazado con HTTP 400 por enviar un cuerpo a `_refresh`. Se corrigió la llamada y se repitió la preparación antes de detener servicios. No fue un fallo del stack ni se cuenta como prueba aprobada. No se volvió a ejecutar pytest ni se generó tráfico adicional con el script en estos ensayos; la suite previa conserva 149 aprobadas.

El equipo debe revisar el informe y la declaración de IA. Para presentar, mantener Docker activo, renovar SSO si expiró y seleccionar explícitamente el intervalo explicado. Los servicios quedaron activos.
