# Trabajo y revisión del equipo — Fase 3

La configuración de ELK, Heartbeat, Kibana y el análisis ya se preparó con asistencia de IA bajo la ampliación de autorización registrada en `docs/sources/aclaraciones-fase-3.md`. Este documento registra el estado de las piezas y la revisión que corresponde al equipo antes de entregar. Las comprobaciones históricas constan en `docs/uso-de-ia.md` y `docs/informe-fase-3.md`.

| Pieza | Estado en el repositorio |
| --- | --- |
| Elasticsearch, Kibana, Filebeat y Heartbeat | Configurados en `docker-compose.yml`, con versión 9.5.5 por defecto; ejecución local documentada el 2026-11-10. |
| Ingesta de logs reales | `elk/filebeat/filebeat.yml` lee CloudWatch de preproducción; se documentó llegada a Elasticsearch con campos tipados. |
| Heartbeat | `elk/heartbeat/heartbeat.yml` contiene cuatro monitores; se documentó una caída y recuperación controladas de la API simulada. |
| Dashboard | `elk/kibana/saved-objects.ndjson` contiene dos vistas de datos, ocho visualizaciones y un dashboard; hay captura en `evidencias/capturas/dashboard-kibana.png`. |
| Logs auténticos | `evidencias/api-local.log` tiene 64 líneas y `evidencias/api-preprod.log` 1274; sus hashes coinciden con los metadatos de ejecución. |
| Informe | `docs/informe-fase-3.md` es un borrador basado en la ejecución del 2026-11-10. |

## Revisión antes de entregar

- [ ] Revisar y poder explicar Compose, credenciales temporales de lectura, recolección, mapeos, monitores y filtros del dashboard.
- [ ] Repetir el arranque desde una copia limpia si la entrega exige reproducibilidad en otro equipo; comprobar permisos, persistencia, importación e ingesta actual.
- [ ] Confirmar en Kibana los siete campos exigidos, la conversión de `event.duration` de ns a ms y el estado up/down de Heartbeat.
- [ ] Revisar el informe, la captura y sus ventanas temporales; conservar las cifras según los intervalos indicados.
- [ ] Completar la declaración final de IA y reunir la entrega en el formato solicitado por el curso.

Guías de ejecución: `docs/elk.md` y `docs/fase-3/SETUP.md`.
