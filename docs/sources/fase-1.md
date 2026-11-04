Admin. y Mantenimiento de Sistemas

**Proyecto de Curso Fase 1** 

**Definición del servicio y diseño de la mesa de servicio**

Nelson García Bravatti 22434  
Sergio Orellana 221122  
Rodrigo Mansilla 22611  
Joaquín Puente 22296  
Gabriel Paz 221087

**CupónManía: Servicio de compra de cupones digitales**

Origen del servicio: servicio desarrollado por dos integrantes del equipo 

**1\. Ficha del servicio**

Descripción del servicio

El servicio permite a comercios afiliados atraer nuevos clientes y generar ventas mediante la publicación de promociones y cupones de descuento que pueden ser descubiertos y comprados por consumidores finales. Una vez confirmada la compra, el consumidor recibe un cupón digital representado por un código QR, el cual puede presentar en el establecimiento para que el comercio valide su vigencia y realice el canje. De esta manera, el comercio obtiene un canal adicional de promoción y adquisición de clientes, mientras que el consumidor accede a productos o servicios con condiciones promocionales claramente definidas.

Cliente

Comercio afiliado: Es la organización que contrata o acepta las condiciones comerciales de la plataforma con el objetivo de publicar promociones, atraer consumidores y generar ventas. Define las condiciones de sus cupones, tales como precio, descuento, vigencia, cantidad disponible y restricciones de uso, y asume la tarifa, comisión o esquema comercial acordado con la plataforma.

Usuarios

Existen dos tipos principales de usuarios.

El consumidor final utiliza la plataforma para descubrir promociones, comprar cupones, consultar sus cupones disponibles y presentar el código QR al momento del canje.

El personal autorizado del comercio utiliza la plataforma para administrar promociones y validar los códigos QR presentados por los consumidores.

Patrocinador

Gerencia General de la empresa operadora de la plataforma.

Este rol financia y respalda el servicio, define sus objetivos de negocio y autoriza las inversiones necesarias para su operación, crecimiento y mejora.

Resultado habilitado para el cliente

El servicio habilita al comercio para convertir una promoción en una venta medible y verificable, alcanzando consumidores que posiblemente no habrían visitado el establecimiento por otros medios. Además, permite conocer cuántos cupones fueron publicados, vendidos y efectivamente canjeados, proporcionando trazabilidad sobre el desempeño de las promociones.  
Utilidad

La utilidad del servicio consiste en permitir que los comercios creen y publiquen promociones, que los consumidores las encuentren y compren, y que cada compra genere un cupón digital que pueda validarse y canjearse una sola vez.

En términos de necesidad resuelta, el comercio obtiene un canal para promocionarse y atraer clientes, mientras que el consumidor obtiene acceso centralizado a descuentos verificables.

Garantía

Disponibilidad: las funciones críticas de consulta, compra, generación de QR y validación estarán disponibles al menos el 99.9% de los minutos elegibles de cada mes, excluyendo únicamente mantenimientos previamente anunciados.

Capacidad: como objetivo inicial de diseño, la infraestructura deberá soportar al menos 1,000 usuarios concurrentes y 50 operaciones de validación de QR por segundo sin superar un tiempo de respuesta de 2 segundos en el percentil 95\.

Continuidad: se plantea un RTO máximo de 2 horas para las funciones críticas y un RPO de 15 minutos para la información transaccional. Esto implica contar con copias de seguridad y procedimientos documentados de recuperación.

Seguridad: las comunicaciones deberán utilizar cifrado en tránsito, existirán controles de acceso según rol, cada QR tendrá un identificador no reutilizable y todo intento de canje quedará auditado. La plataforma no deberá almacenar directamente datos completos de tarjetas si estos pueden ser gestionados mediante tokenización por la pasarela de pagos.

**2\. Las cuatro dimensiones aplicadas**

2.1 Organización y personas

Elemento 1: propietario del servicio.

Debe existir un Service Owner responsable del desempeño integral de la plataforma. Este rol revisa niveles de servicio, riesgos, incidentes importantes, capacidad, satisfacción del cliente y oportunidades de mejora. Su existencia es verificable mediante la matriz de responsabilidades del servicio, los reportes mensuales y la asignación de propietario en la herramienta de gestión.

Elemento 2: equipo de atención a comercios y consumidores.

Debe existir una mesa de servicio responsable de recibir incidentes y solicitudes. El personal de primer nivel debe estar capacitado para identificar al usuario, consultar compras, verificar estados de cupones, restablecer accesos y aplicar soluciones temporales documentadas. Es verificable mediante los registros de tickets, procedimientos de atención, base de conocimiento y asignación de casos.

Elemento 3: equipo técnico especializado.

El servicio requiere personal con conocimientos de aplicación, base de datos, infraestructura, integraciones, seguridad y pasarela de pagos. Estos especialistas participan cuando el primer nivel no cuenta con capacidad técnica suficiente. Puede verificarse mediante los grupos N2 y N3 definidos en la herramienta de soporte y las reglas de escalamiento.

Elemento 4: capacitación del personal del comercio.

Los trabajadores encargados del canje necesitan conocer el procedimiento correcto para escanear, verificar y confirmar un cupón. Una validación incorrecta puede producir doble canje, rechazo de un cupón válido o entrega de productos sin registrar la transacción. Debe existir material de capacitación y un procedimiento de canje accesible para cada comercio.

2.2 Información y tecnología

Elemento 1: información de cupones.

Por cada cupón deben conservarse como mínimo el comercio que lo ofrece, descripción, precio, descuento, condiciones de uso, fecha de inicio, fecha de expiración, cantidad disponible y estado de publicación. Estos campos pueden verificarse directamente en la base de datos y en el panel administrativo.

Elemento 2: información transaccional.

Por cada compra debe existir un identificador único, usuario comprador, cupón adquirido, estado del pago, fecha de compra, estado del QR, fecha de canje y comercio que realizó la validación. Esta información permite reconstruir una transacción y resolver disputas.

Elemento 3: componentes tecnológicos críticos.

La solución necesita como mínimo aplicación web o móvil, API de negocio, servicio de autenticación, base de datos, servicio de generación y validación de QR, integración con pasarela de pagos y mecanismos de notificación. Las dependencias deben documentarse porque la falla de cualquiera de las que participan en compra o canje puede afectar la utilidad completa del servicio.

Elemento 4: monitoreo y trazabilidad.

Deben existir métricas de disponibilidad, tiempo de respuesta, errores HTTP, pagos rechazados por causa técnica, generación de QR y validaciones de cupones. Los eventos deben contener identificadores de correlación que permitan seguir una operación desde la compra hasta el canje.

2.3 Socios y proveedores

Elemento 1: proveedor de pagos.

La pasarela de pagos procesa el cobro de los cupones. Su indisponibilidad puede impedir que un consumidor complete una compra aunque el resto de la plataforma continúe funcionando. Debe existir un contrato que especifique disponibilidad, tiempos de respuesta ante incidentes, tratamiento de transacciones duplicadas y procedimiento de conciliación.

Elemento 2: proveedor de infraestructura.

La plataforma puede depender de un proveedor de nube para cómputo, bases de datos, almacenamiento, copias de seguridad y conectividad. Deben documentarse la disponibilidad contratada, regiones utilizadas, mecanismos de respaldo y procedimiento de atención de incidentes.

Elemento 3: proveedores de comunicación.

El correo electrónico, SMS o servicio de notificaciones utilizado para confirmar compras también representa una dependencia externa. Una falla de notificación no necesariamente invalida la compra, por lo que el cupón deberá continuar disponible dentro de la cuenta del usuario aunque el mensaje externo no pueda entregarse.

Elemento 4: los comercios afiliados.

Aunque sean clientes, también participan activamente en la entrega del valor. La plataforma puede generar correctamente el cupón, pero el servicio pierde valor si el comercio no capacita a su personal o se niega incorrectamente a aceptar un cupón válido. Por ello, el contrato con el comercio debe establecer condiciones de publicación, aceptación y canje.

2.4 Flujos de valor y procesos

Elemento 1: incorporación de comercios.

El comercio solicita su registro, se valida la información necesaria, se crea la cuenta, se asignan permisos y se habilita la publicación de promociones. El proceso puede verificarse mediante el registro de altas y los tiempos de activación.

Elemento 2: publicación de cupones.

El comercio configura una promoción, se validan sus campos y condiciones, se publica y se vuelve visible para los consumidores. Deben conservarse las versiones relevantes de sus términos para evitar que una condición se modifique después de que un consumidor ya compró.

Elemento 3: compra y emisión.

El consumidor selecciona un cupón, inicia el pago, la pasarela confirma la transacción, la plataforma registra la compra y genera un identificador QR asociado al cupón adquirido. La operación debe ser idempotente para evitar cobrar dos veces o emitir dos cupones ante reintentos.

Elemento 4: validación y canje.

El comercio escanea el QR, la plataforma comprueba autenticidad, vigencia, propietario, estado y restricciones y, si todo es correcto, registra el cupón como canjeado. La validación y el cambio de estado deben realizarse de forma atómica para impedir el doble uso.

Elemento 5: soporte y mejora.

Incidentes y solicitudes ingresan por la mesa de servicio. Los incidentes recurrentes alimentan gestión de problemas y, cuando la corrección implica modificar el servicio, se genera una solicitud de cambio. La actividad de entregar y soportar incluye precisamente la operación diaria, monitoreo, gestión de incidentes y cumplimiento de solicitudes.

Factor externo del entorno: legal/regulatorio.

La plataforma opera con promociones, pagos, información personal y condiciones comerciales, por lo que debe ajustarse a las obligaciones de protección al consumidor, comercio electrónico, facturación, privacidad y medios de pago que sean aplicables en el país donde opere.

Este factor condiciona el servicio porque las reglas de expiración, devolución, tratamiento de datos y presentación de términos no pueden definirse únicamente por conveniencia técnica. Además, deben conservarse evidencias de qué condiciones aceptó el consumidor y del momento en que se produjo una compra o canje. 

**3\. Catálogo de servicio**

| Solicitudes de servicio | Incidentes tipificados |
| ----- | ----- |
| Alta o modificación de comercio. Descripción: crear un nuevo comercio, sucursal o actualizar información de uno existente. Quién puede solicitarlo: administrador autorizado del comercio. Justificación: nada se encuentra averiado; el usuario solicita una acción prevista en el catálogo. | Compra de cupón no disponible. Descripción: un consumidor intenta adquirir un cupón publicado y el proceso falla por una causa técnica. Quién puede reportarlo: consumidor, comercio o monitoreo. Justificación: una función previamente disponible presenta una interrupción o reducción de calidad. |
| Publicación o modificación de cupón. Descripción: solicitar el alta o cambio de una promoción, precio, vigencia o cantidad disponible. Quién puede solicitarlo: administrador autorizado del comercio. Justificación: es trabajo normal y predefinido solicitado por el cliente. | Pago confirmado pero QR no generado. Descripción: la transacción fue aprobada, pero el consumidor no recibe un cupón utilizable. Quién puede reportarlo: consumidor, comercio o monitoreo. Justificación: la compra debía producir un QR y el servicio no entregó el resultado esperado. |
| Restablecimiento o desbloqueo de cuenta. Descripción: recuperar acceso a una cuenta existente siguiendo el procedimiento de verificación de identidad. Quién puede solicitarlo: consumidor o usuario autorizado del comercio. Justificación: corresponde a una petición repetible con procedimiento conocido y no necesariamente a una falla de la plataforma. | QR válido no puede ser canjeado. Descripción: el comercio intenta validar un cupón vigente y no utilizado, pero el sistema no permite completar el canje. Quién puede reportarlo: personal autorizado del comercio o consumidor afectado. Justificación: una función comprometida del servicio presenta una interrupción o degradación. |
| Reembolso o cancelación según política. Descripción: tramitar la devolución de una compra que cumple las condiciones de cancelación definidas. Quién puede solicitarlo: consumidor propietario de la compra. Justificación: es una petición de negocio prevista; no implica que el sistema esté roto. | Plataforma indisponible o con degradación severa. Descripción: usuarios no pueden iniciar sesión, consultar promociones o utilizar funciones críticas, o el tiempo de respuesta supera repetidamente el nivel acordado. Quién puede reportarlo: cualquier usuario o monitoreo. Justificación: existe interrupción o reducción no planificada de la calidad del servicio. |

**4\. Diseño de service desk**  
Service Desk virtual.

El personal puede encontrarse físicamente distribuido pero opera como una única mesa mediante una herramienta común de tickets, una base de conocimiento y procedimientos compartidos.

Este modelo se adapta al servicio porque tanto consumidores como comercios acceden digitalmente y los incidentes normalmente no requieren intervención física en una sede. También permite incorporar especialistas o personal de guardia sin que deban encontrarse en un único lugar.

El material del curso distingue los modelos local, centralizado, virtual y follow-the-sun; el modelo virtual permite que personal distribuido funcione como una sola mesa, aunque exige disciplina en el registro de información.

Canales de contacto

Portal web o formulario dentro de la aplicación: canal principal y recomendado porque permite identificar al usuario y asociar automáticamente compra, comercio o cupón.

Correo electrónico: atención de casos que no requieren interacción inmediata.

Chat de soporte: atención rápida durante el horario de la mesa.

Teléfono de emergencia para comercios: utilizado exclusivamente para incidentes P1 o situaciones donde el canje esté detenido de manera generalizada.

Monitoreo automático: puede crear tickets sin intervención de un usuario cuando se detecte indisponibilidad, aumento de errores o degradación.

Horario de atención

Atención regular de la mesa de servicio: 07:00 a 22:00, todos los días, zona horaria America/Guatemala, UTC-6.

Para incidentes P1 existe guardia técnica N2/N3 las 24 horas, los 365 días del año.

Fuera del horario regular, los incidentes P1 detectados por monitoreo o reportados mediante el canal de emergencia se registran en la misma herramienta de tickets y se enrutan directamente a la guardia N2/N3, manteniendo trazabilidad dentro del Service Desk. 

Los tiempos de P1 corren de forma continua. Para P2, P3 y P4 el reloj de soporte se contabiliza únicamente dentro del horario regular declarado.

Niveles de atención

N1 – Mesa de servicio. Responsable de recibir y registrar todo caso, verificar identidad, clasificar, priorizar, atender solicitudes estándar y resolver incidentes mediante procedimientos o soluciones temporales documentadas. Ejemplos: restablecimiento de contraseña, revisión de estado de compra, reenvío de información del cupón o aplicación de una solución conocida.

N2 – Soporte de aplicación y operaciones. Responsable de incidentes que requieren conocimiento de la aplicación, API, integraciones, base de datos o infraestructura. Analiza registros, métricas y transacciones, aplica mitigaciones y determina si existe un defecto que requiere participación de ingeniería.

N3 – Ingeniería y proveedores especializados. Responsable de defectos de software, modificaciones de arquitectura, problemas complejos de datos y fallas que requieran intervención del proveedor. Puede preparar hotfixes, correcciones permanentes o solicitudes de cambio.  
El esquema N1/N2/N3 mantiene la misma lógica utilizada en el material práctico del curso: N1 resuelve con procedimientos; N2 atiende aplicación, integraciones y datos; N3 atiende defectos o dependencias especializadas.

Matriz de escalamiento

| Ruta | Disparador | Origen | Rol receptor | Resultado esperado |
| ----- | ----- | ----- | ----- | ----- |
| Funcional | N1 no puede resolver mediante procedimiento conocido, la causa está en aplicación/integración/datos o transcurrieron 10 minutos de un P1 sin restauración | N1 | N2 – Soporte de aplicación | Incorporar mayor conocimiento técnico |
| Funcional | Existe defecto de software, se requiere modificar código, intervenir infraestructura especializada o actuar con un proveedor | N2 | N3 – Ingeniería/proveedor | Incorporar capacidad especializada y definir corrección |
| Jerárquico | Se declara un incidente P1 | Cualquier nivel | Service Manager | Coordinar áreas, comunicaciones y decisiones de negocio |
| Jerárquico | Se ha consumido 75% del tiempo objetivo de resolución sin una restauración prevista | N1/N2/N3 | Service Manager | Evitar incumplimiento y asignar recursos adicionales |
| Jerárquico | La solución requiere presupuesto extraordinario, aceptación de riesgo, suspensión temporal de una función o decisión contractual | Service Manager | Service Owner / patrocinador | Obtener autoridad para tomar la decisión |
| Jerárquico | Se incumple formalmente un SLA o existe reincidencia grave | Service Manager | Service Owner y patrocinador | Definir acciones correctivas y responsabilidad |

**5\. Flujos de atención**

5.1 Flujo de gestión de incidentes

5.2 Flujo de solicitud de servicio

5.3 Flujo de gestión de problemas

5.4 Flujo de habilitación del cambio

**6\. Matriz de priorización**

Criterios de impacto

Impacto alto: la compra o el canje se encuentra indisponible para toda la plataforma, están fallando al menos 20% de las transacciones críticas observadas durante 10 minutos consecutivos o se encuentran afectados 50 o más comercios simultáneamente.

Impacto medio: están afectados entre 5 y 49 comercios o entre 5% y 19.9% de las transacciones críticas. El servicio continúa parcialmente disponible o existe una alternativa temporal.

Impacto bajo: afecta a un máximo de 4 comercios o a usuarios individuales y no detiene de forma general la compra o el canje.

Criterios de urgencia

Urgencia alta: existe una transacción activa bloqueada que requiere recuperación inmediata, hay cupones que expirarán en menos de 2 horas, existe riesgo de doble canje, fraude o pérdida financiera que continúa aumentando.

Urgencia media: el servicio está degradado pero existe una solución temporal, o la afectación puede esperar hasta el mismo día sin perder el valor del cupón.

Urgencia baja: no existe transacción crítica bloqueada, hay workaround suficiente y la situación puede esperar más de 24 horas.

| Impacto \\ Urgencia | Alta | Media | Baja |
| ----- | ----- | ----- | ----- |
| Alto | P1 – Respuesta: 15 min. Resolución: 2 h | P2 – Respuesta: 30 min. Resolución: 4 h | P3 – Respuesta: 4 h. Resolución: 1 día hábil |
| Medio | P2 – Respuesta: 30 min. Resolución: 4 h | P3 – Respuesta: 4 h. Resolución: 1 día hábil | P4 – Respuesta: 8 h. Resolución: 3 días hábiles |
| Bajo | P3 – Respuesta: 4 h. Resolución: 1 día hábil | P4 – Respuesta: 8 h. Resolución: 3 días hábiles | P4 – Respuesta: 8 h. Resolución: 3 días hábiles |

**7\. Acuerdos de nivel de servicio**

Acuerdo

Cliente: comercios afiliados.

Proveedor: empresa operadora de la Plataforma de Cupones Digitales y Canje QR.

Alcance: publicación de cupones, compra, emisión del cupón digital, consulta y validación/canje.

Ventana del servicio: 24 horas al día, 365 días al año.

Ventana regular de soporte: 07:00 a 22:00, America/Guatemala.

Soporte de incidentes P1: 24x7.

Mantenimiento planificado: podrá excluirse de la medición de disponibilidad únicamente cuando sea informado con al menos 72 horas de anticipación. Las ventanas de mantenimiento no deberán utilizarse para excluir fallas no planificadas.

Un buen objetivo de nivel de servicio debe indicar qué se mide, cómo se calcula, la ventana de evaluación y el umbral. Además, para experiencia y rendimiento es preferible utilizar percentiles cuando corresponda en lugar de esconder casos lentos dentro de un promedio.

Objetivos de nivel de servicio

| Objetivo | Qué se mide | Cómo se calcula | Ventana de evaluación | Umbral |
| ----- | ----- | ----- | ----- | ----- |
| SLO 1 – Disponibilidad transaccional | Disponibilidad de las funciones críticas de compra, emisión de QR y validación/canje | Minutos en que las funciones críticas se encuentran disponibles / minutos elegibles del período × 100\. Se excluyen únicamente mantenimientos previamente anunciados | Mes calendario | Igual o mayor a 99.9% |
| SLO 2 – Respuesta a incidentes P1 | Tiempo entre la creación/detección de un P1 y el reconocimiento por una persona responsable | Número de P1 reconocidos en 15 minutos o menos / total de P1 del mes × 100 | Mes calendario, reloj 24x7 | Al menos 95% de los P1 dentro de 15 minutos |
| SLO 3 – Restauración de incidentes P1 | Tiempo desde apertura de un P1 hasta restauración de la función afectada, aunque la causa raíz aún no esté corregida | Número de P1 restaurados en 2 horas o menos / total de P1 del mes × 100 | Mes calendario, reloj 24x7 | Al menos 90% de los P1 restaurados dentro de 2 horas |
| SLO 4 – Rendimiento de validación QR | Tiempo que tarda la plataforma en responder una solicitud técnicamente válida de validación de QR | Se ordenan los tiempos de respuesta de todas las validaciones elegibles y se calcula el percentil 95 | Mes calendario | Percentil 95 igual o menor a 2 segundos |

Acuerdos de nivel operativo que sostienen el SLA

| OLA interno | Compromiso | SLA que sostiene |
| ----- | ----- | ----- |
| Monitoreo → Mesa de servicio | Una alarma crítica debe crear el ticket y notificar a la guardia en un máximo de 2 minutos | SLO 1, SLO 2 y SLO 3 |
| N1 → N2 | Un P1 debe escalarse funcionalmente a N2 como máximo 10 minutos después de su detección si N1 no logra restaurarlo | SLO 2 y SLO 3 |
| N2 – Soporte de aplicación | Debe reconocer un P1 en máximo 10 minutos desde la notificación e iniciar diagnóstico inmediatamente | SLO 2 y SLO 3 |
| N2 → N3 | Cuando exista indicio de defecto, N3 debe ser convocado antes de que transcurran 30 minutos desde la apertura del P1 | SLO 3 |
| N3 – Ingeniería | Debe proporcionar una decisión de mitigación, rollback o corrección de emergencia en un máximo de 60 minutos desde su incorporación | SLO 3 |
| Infraestructura y base de datos | Componentes internos críticos con disponibilidad mensual mínima de 99.99%, respaldo de información transaccional cada 15 minutos y procedimiento probado de recuperación | SLO 1 y continuidad |
| Aplicación de validación | Procesamiento interno de QR con p95 máximo de 1.2 segundos y consulta principal de datos con p95 máximo de 300 ms | SLO 4 |

Dependencias externas

La pasarela de pagos no debería documentarse como OLA porque no pertenece a un equipo interno. Se debe mantener un contrato de soporte o UC con el proveedor.

Como requisito de diseño, el contrato debería comprometer disponibilidad de al menos 99.95% mensual para la API de pagos y respuesta a incidentes críticos en un máximo de 15 minutos. Esto evita comprometer al comercio con una disponibilidad que una dependencia crítica externa no puede sostener.

Los objetivos de disponibilidad de los componentes internos y dependencias externas se establecerán con margen suficiente para que la disponibilidad combinada de la ruta transaccional pueda sostener el 99.9% comprometido al cliente. 

Procedimiento ante incumplimiento

Los resultados del SLA serán revisados mensualmente por el Service Owner y el responsable de relación con comercios.

Cuando un objetivo incumpla su umbral, deberá abrirse un registro de problema como máximo el siguiente día hábil. Se realizará análisis de causa y se documentará un plan de acción con responsable y fecha de cumplimiento en un máximo de cinco días hábiles.

Si el mismo objetivo se incumple durante dos meses consecutivos, el caso se elevará al patrocinador del servicio. Se revisarán capacidad, arquitectura, procedimientos y contratos de proveedores y podrán suspenderse cambios no críticos que incrementen el riesgo hasta completar las acciones correctivas.

Si el incumplimiento se origina en un proveedor externo, además del problema interno se deberá activar el procedimiento de incumplimiento definido en su contrato y revisar si los niveles contratados continúan siendo suficientes.

De esta manera existe una cadena coherente: el cliente recibe un compromiso medible mediante el SLA; cada equipo interno tiene tiempos más exigentes mediante OLA; y las dependencias externas se controlan mediante contratos de soporte. La distinción SLA–OLA–UC forma parte explícita de la terminología utilizada en el curso.

**Declaración de uso de inteligencia artificial**

Se utilizaron herramientas de inteligencia artificial para revisar la cobertura del documento respecto de las instrucciones del proyecto, apoyar la organización de ideas y revisar la redacción. Las decisiones sobre el diseño de la mesa de servicio, los objetivos de nivel de servicio y la construcción final de los flujos fueron elaboradas y validadas por nuestro equipo. 