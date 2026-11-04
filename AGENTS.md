# Instrucciones de Codex para CupónManía Fase 3

Lee `instructions.md` completo, luego `docs/sources/aclaraciones-fase-3.md`. Consulta los documentos de Fase 1 y Fase 2 cuando necesites verificar el catálogo o la relación con Jira. La decisión de esta fase está cerrada: **no existe una API propia disponible; construir API simulada**. No buscar claves, repositorios privados ni integraciones reales.

## Qué puedes implementar

- API simulada de CupónManía con ocho endpoints de negocio, respuestas 2xx/4xx/5xx, latencia variable y logs JSON automáticos.
- Generador continuo de tráfico HTTP contra esos endpoints.
- Pruebas, documentación reproducible y, si es útil, Dockerfiles individuales para API y generador.
- Muestra `.log` producida de verdad al ejecutar el código, nunca inventada.

## Qué NO puedes implementar

La aclaración académica reserva al equipo: configuración de Elasticsearch, Filebeat/Logstash, Kibana y Heartbeat, `docker-compose.yml`, `heartbeat.yml`, diseño real del dashboard y análisis de resultados. No editar esos archivos, no generar plantillas completas ni scripts que los produzcan. Puedes documentar interfaces necesarias para que el equipo realice conexiones; evita hacer ese trabajo por ellos.

No crear frontend (React, Next.js, HTML) ni dashboard UI alternativo. Toda la visualización se realizará en Kibana. **No activar ni invocar una skill de diseño UI.** No crear tickets reales en Jira desde tráfico simulado.

## Coordinación con subagentes

- Principal: fija `docs/contracts.md` y coordina los archivos compartidos.
- `api_builder`: `api/`, `docs/api.md`.
- `traffic_builder`: `traffic/`, `docs/traffic.md`.
- `api_qa`: `tests/integration/`, `docs/qa-api-traffic.md`.

El principal debe permitir que API y tráfico se desarrollen de manera paralela solo después de fijar el contrato; integrar y verificar al final. No permitir escrituras concurrentes sobre el mismo archivo. Si no hay soporte de subagentes, trabajarlo secuencialmente e informarlo.

## Calidad, seguridad y honestidad

Usar pruebas (TDD si la skill está disponible), operaciones ficticias, límites de tasa, tiempo real medido, `event.duration` en nanosegundos y logs reales sin secretos. No hacer instalaciones globales, commits ni pushes sin autorización. Registrar la asistencia de IA en `docs/uso-de-ia.md`. No afirmar que ELK, Heartbeat o el dashboard ya funcionan antes de que el equipo los valide.
