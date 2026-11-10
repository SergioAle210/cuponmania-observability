# Instrucciones de Codex para CupónManía Fase 3

Lee `docs/fase-3/instructions.md` completo, luego `docs/sources/aclaraciones-fase-3.md`. Consulta los documentos de Fase 1 y Fase 2 cuando necesites verificar el catálogo o la relación con Jira. Decisión del equipo (2026-11-09), que sustituye a la anterior: **se usa la API real de CupónManía en preproducción** (`https://api-preprod.cuponmania.com.gt`, logs ECS en CloudWatch). La API simulada se conserva como alternativa local y para pruebas. El generador apunta a la API real con `--target real` (ver `docs/traffic.md`); no usar credenciales de clientes ni crear datos reales.

## Qué puedes implementar

- API simulada de CupónManía con ocho endpoints de negocio, respuestas 2xx/4xx/5xx, latencia variable y logs JSON automáticos.
- Generador continuo de tráfico HTTP contra esos endpoints.
- Pruebas, documentación reproducible y, si es útil, Dockerfiles individuales para API y generador.
- Muestra `.log` producida de verdad al ejecutar el código, nunca inventada.

## Stack ELK, dashboard y análisis

La regla original reservaba al equipo la configuración de Elasticsearch, Filebeat, Kibana y Heartbeat, el `docker-compose.yml`, el dashboard y el análisis. **El catedrático amplió en persona esa autorización** (comunicada el 2026-11-09, registrada en `docs/sources/aclaraciones-fase-3.md`, sección *Ampliación del uso de IA*): el asistente puede construir esas piezas y redactar el análisis. Condiciones:

- Declarar cada pieza en `docs/uso-de-ia.md` y en el apartado final del informe.
- El análisis usa solo datos realmente observados en Elasticsearch/Kibana; nunca cifras, capturas o resultados inventados.
- El equipo revisa, ejecuta y puede explicar cada configuración antes de entregarla.

No crear frontend (React, Next.js, HTML) ni dashboard UI alternativo. Toda la visualización se realizará en Kibana. **No activar ni invocar una skill de diseño UI.** No crear tickets reales en Jira desde tráfico simulado.

## Coordinación con subagentes

- Principal: fija `docs/contracts.md` y coordina los archivos compartidos.
- `api_builder`: `api/`, `docs/api.md`.
- `traffic_builder`: `traffic/`, `docs/traffic.md`.
- `api_qa`: `tests/integration/`, `docs/qa-api-traffic.md`.

El principal debe permitir que API y tráfico se desarrollen de manera paralela solo después de fijar el contrato; integrar y verificar al final. No permitir escrituras concurrentes sobre el mismo archivo. Si no hay soporte de subagentes, trabajarlo secuencialmente e informarlo.

## Calidad, seguridad y honestidad

Usar pruebas (TDD si la skill está disponible), operaciones ficticias, límites de tasa, tiempo real medido, `event.duration` en nanosegundos y logs reales sin secretos. No hacer instalaciones globales, commits ni pushes sin autorización. Registrar la asistencia de IA en `docs/uso-de-ia.md`. No afirmar que ELK, Heartbeat o el dashboard funcionan sin haberlos ejecutado y comprobado.
