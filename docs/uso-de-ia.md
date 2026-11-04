# Registro del uso de inteligencia artificial

## Preparación de instrucciones

Se utilizó ChatGPT para revisar y organizar el enunciado de Fase 3, recopilar el contexto de Fases 1 y 2 y preparar un prompt, archivos de instrucciones y una guía de navegación de Kibana.

## Parte de implementación permitida

Se permite el uso de IA para construir la API simulada y el generador continuo de tráfico. Registrar a continuación la asistencia **realmente recibida**:

| Fecha | Herramienta | Para qué se utilizó | Archivos modificados | Revisión/pruebas realizadas |
| --- | --- | --- | --- | --- |
| 2026-11-03 (Guatemala) | Codex, coordinador | Lectura de instrucciones y catálogo; contrato de ocho operaciones y logs; entorno local aislado con Python 3.13.5 existente; coordinación, documentación de ejecución e integración prevista | `docs/contracts.md`, `docs/fase-3/SETUP.md`, `requirements-dev.txt`, `pytest.ini`, `.dockerignore`, `.gitignore`, esta bitácora y evidencia local | Resultados concretos se registran en `docs/qa-api-traffic.md`; Docker no ejecutado |
| 2026-11-03 (Guatemala) | Subagente `api_builder` | Implementación FastAPI de operaciones ficticias, perfiles configurables, medición monotónica y logs JSON; pruebas unitarias; Dockerfile de API | `api/`, `docs/api.md` | Pruebas locales documentadas en `docs/qa-api-traffic.md`; imagen pendiente |
| 2026-11-03 (Guatemala) | Subagente `traffic_builder` | Generador HTTP continuo/finito, límites de tasa y concurrencia, escenarios, apagado, pruebas unitarias y Dockerfile del generador | `traffic/`, `docs/traffic.md` | Pruebas locales documentadas en `docs/qa-api-traffic.md`; imagen pendiente |
| 2026-11-03 (Guatemala) | Subagente `api_qa` | Pruebas de integración local por HTTP real, correspondencia entre respuestas y logs, cobertura y resiliencia del generador | `tests/integration/`, `docs/qa-api-traffic.md` | Comandos, resultados y límites de las verificaciones se registran en el documento de QA |

El contrato se fijó antes de implementar API y tráfico en paralelo. `api_qa` comenzó después de terminar ambos módulos, según el reparto de archivos. No hay una skill específica de TDD en el catálogo de esta sesión; se escribieron pruebas automatizadas propias sin instalar skills. No se utilizó ninguna skill de UI.

El comando genérico `python` apuntaba a 3.7.9; se comprobó la instalación existente 3.13.5 por ruta absoluta y se creó `.venv` dentro del proyecto. Las dependencias se descargaron de PyPI únicamente en ese entorno (usando `uv`, ya instalado); no se instalaron herramientas globalmente ni se modificó el PATH. La primera descarga aislada falló por DNS y el segundo intento autorizado completó la instalación. No se ejecutó ningún comando Docker, ni se hicieron commits o pushes.

La verificación final local ejecutó **119 pruebas aprobadas y una advertencia de deprecación de Starlette/TestClient en 21.48 s**, con salida guardada en `evidencias/pruebas-locales.txt`. Incluye 57 casos unitarios de API, 54 del generador y 8 de integración TCP. Las pruebas necesitaron permisos de ejecución fuera del aislamiento de la herramienta por un bloqueo de sockets internos de asyncio en Windows; continuaron usando solamente procesos locales.

El coordinador ejecutó además Uvicorn y el generador sobre TCP loopback para producir `evidencias/api-local.log`: **64 eventos auténticos**, ocho por endpoint. `evidencias/generador-local.json` conserva el resumen del cliente y `evidencias/ejecucion-local.json` registra configuración, comando, tiempos UTC y SHA-256. No se editaron ni completaron manualmente líneas del `.log`. Estos conteos acreditan ejecución del software; no constituyen interpretación del monitoreo ni evidencia de ELK/Heartbeat/Kibana.

## Trabajos reservados al equipo

Conforme a las aclaraciones recibidas, la configuración de Elasticsearch/Filebeat/Heartbeat/Kibana, la construcción visual del dashboard y la interpretación de los resultados corresponden al equipo. No presentar configuración/diseño generados por IA como trabajo propio ni inventar resultados de pruebas.

Esta bitácora orienta el apartado final del informe técnico; el equipo debe adaptarla a lo que realmente haga.
