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

## Verificación técnica en esta computadora — 2026-11-15

La conexión SSO/CloudWatch, la ingesta actual y los ocho paneles de Kibana se verificaron aquí. También pasaron caída y recuperación de la API simulada (45 s, tres chequeos down), reinicio de Filebeat sin nuevos duplicados en una ventana de 8755 eventos, y persistencia de esos documentos y los 11 objetos de Kibana tras recrear los cuatro contenedores de observabilidad con sus volúmenes. No se reimportaron los objetos durante la prueba. Evidencias: `evidencias/2026-11-15-pruebas-stack/README.md`.

Los cuatro monitores quedaron up y los servicios activos. Hay un par de eventos idénticos que ya estaba en CloudWatch, documentado como calidad del origen; no fue creado por los reinicios. El entorno está técnicamente listo para la demostración en esta máquina. La lista siguiente corresponde a revisión y preparación del equipo, no a fallos de esas pruebas.

## Revisión antes de entregar

- [ ] Revisar y poder explicar Compose, credenciales temporales de lectura, recolección, mapeos, monitores y filtros del dashboard.
- [ ] Repetir el arranque desde una copia limpia si la entrega exige reproducibilidad en otro equipo; comprobar permisos, persistencia, importación e ingesta actual.
- [ ] Repasar en equipo los siete campos exigidos, la conversión de `event.duration` de ns a ms y el estado up/down de Heartbeat, ya comprobados técnicamente en esta máquina.
- [ ] Revisar el informe, la captura y sus ventanas temporales; conservar las cifras según los intervalos indicados.
- [ ] Completar la declaración final de IA y reunir la entrega en el formato solicitado por el curso.

Guías de ejecución: `docs/elk.md` y `docs/fase-3/SETUP.md`.
