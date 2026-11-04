# Aclaraciones adicionales de la Fase 3

Texto proporcionado por Sergio junto al PDF. Se conserva separado para distinguirlo del enunciado adjunto.

## Origen de los logs

Los logs que alimentan el monitoreo deben provenir de una API asociada al servicio definido en la Fase 1. Cada equipo puede optar por una de dos vías.

API propia del servicio. Si el servicio cuenta con una API construida por el equipo, se instrumenta esa API.

API simulada del servicio. Si el equipo no cuenta con una API propia, construye una API que simule el servicio. La API simulada cumple con las siguientes condiciones:

- Expone un endpoint por cada elemento del catálogo de servicio entregado en la Fase 1.
- Devuelve respuestas exitosas y respuestas de error (códigos 4xx y 5xx) en una proporción definida y documentada por el equipo.
- Presenta tiempos de respuesta variables entre peticiones.
- Genera los logs automáticamente desde su código, con los campos indicados en el documento de la fase.

## Generador de tráfico

En ambas vías, el tráfico hacia la API se produce mediante un script que ejecuta peticiones de forma continua sobre los endpoints. El script se entrega junto con los demás archivos de la fase. El informe técnico describe la vía elegida, los endpoints, la proporción de errores configurada y el funcionamiento del generador de tráfico.

## Uso de inteligencia artificial

Se permite el uso de asistentes de inteligencia artificial para construir la API simulada y el generador de tráfico, con la condición de declarar en un apartado final del informe técnico para qué se utilizaron. La configuración del stack ELK, el diseño del dashboard y la interpretación de los resultados deben ser propios.
