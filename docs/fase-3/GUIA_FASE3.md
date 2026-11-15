# CupónManía Observability — guía del repositorio

Este repositorio contiene la implementación de la Fase 3: generador de tráfico, API simulada para pruebas, configuración local de Elasticsearch, Kibana, Filebeat y Heartbeat, objetos de Kibana, evidencias e informe técnico en borrador. La fuente principal de logs es la API **real de preproducción** de CupónManía; la decisión del equipo se registró el 2026-11-09.

## Lectura recomendada

1. `docs/fase-3/instructions.md` y `docs/sources/aclaraciones-fase-3.md`: requisitos y autorización vigente.
2. `docs/elk.md`: arquitectura, requisitos y ejecución del stack.
3. `docs/traffic.md`: generador en modo local y `--target real`.
4. `docs/informe-fase-3.md`: resultados observados y límites de la evidencia.
5. `docs/uso-de-ia.md`: registro de asistencia de IA.

`docs/fase-3/PROMPT_CODEX.md` conserva el encargo original de la primera iteración como antecedente histórico. Su prohibición de construir ELK y su decisión de usar solo una API simulada fueron sustituidas por la decisión y la ampliación de autorización posteriores. `docs/pasos-kibana-equipo.md` conserva los pasos manuales de Kibana como referencia; los objetos de Kibana ya están en `elk/kibana/saved-objects.ndjson`.

## Estado documentado

- La API simulada, el generador y las pruebas locales se desarrollaron; `evidencias/api-local.log` conserva 64 eventos genuinos.
- La configuración del stack y el dashboard están en el repositorio. La bitácora `docs/uso-de-ia.md` documenta una ejecución del 2026-11-10 con ingesta de CloudWatch, cuatro monitores Heartbeat, importación de Kibana y captura del dashboard.
- `evidencias/api-preprod.log` conserva 1274 eventos de acceso de la API real. Su hash coincide con `evidencias/ejecucion-preprod.json`.
- El informe técnico sigue siendo un borrador sujeto a revisión del equipo. La ejecución histórica no acredita que los servicios estén activos actualmente ni sustituye la revisión antes de entregar.

La visualización se realiza únicamente en Kibana; no hay frontend propio. Los logotipos de `assets/brand/` son referencias de marca y documentación.
