# Trabajo propio del equipo - Fase 3

Este archivo registra lo que el equipo debe decidir, construir y verificar directamente.

## Infraestructura

- [ ] Elegir y documentar versiones compatibles para Elasticsearch, Kibana, Filebeat y Heartbeat.
- [ ] Elaborar `docker-compose.yml` con los cuatro servicios exigidos y los servicios auxiliares de API/generador, si se utilizan en Docker.
- [ ] Elaborar la configuración Filebeat/Logstash que recolecta los `.log` reales de la API y los envía automáticamente a Elasticsearch.
- [ ] Elaborar `heartbeat.yml` y verificar up/down con una caída y recuperación controladas.
- [ ] Garantizar que la persistencia, redes, credenciales y volúmenes funcionan sin exponer secretos.

## Kibana y métricas

- [ ] Crear la data view sobre el índice real de logs de API.
- [ ] Validar en Discover los siete campos obligatorios con los tipos adecuados.
- [ ] Crear la data view o fuente de datos Heartbeat.
- [ ] Diseñar las seis visualizaciones requeridas y guardar un dashboard completo.
- [ ] Definir error rate y tratamiento de 4xx/5xx, excluir salud del tráfico de negocio.
- [ ] Verificar conversión correcta de `event.duration` a ms.
- [ ] Capturar evidencia del dashboard y su actualización ante tráfico real.

## Informe y entrega

- [ ] Muestra de al menos 50 líneas `.log` generadas automáticamente.
- [ ] Arquitectura, configuración, endpoints, proporciones y funcionamiento del generador.
- [ ] Análisis **propio** de los resultados observados, sin cifras inventadas.
- [ ] Declaración de asistencia de IA al final del informe.
- [ ] Prueba desde una copia limpia y comandos reproducibles.

Guía de navegación: `docs/pasos-kibana-equipo.md`.
