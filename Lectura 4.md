# Observabilidad

## 1. Qué es la observabilidad?

La observabilidad es la capacidad de un sistema de permitir que su estado actual sea estimado a partir de sus salidas. En TI, esto significa que mientras más información generen los sistemas sobre su funcionamiento, más fácil será detectar y entender lo que sucede cuando ocurre un fallo.

## 2. Por qué es importante construir una aplicación observable?

Construir una aplicación observable es importante porque ofrece estos 5 beneficios principales:

-Detección de fallos en entornos complejos: Permite localizar rápidamente el origen de problemas en bases de datos, microservicios o contenedores.

-Control en despliegues continuos (CI/CD): Ayuda a identificar qué salió mal en una nueva implementación y facilita la recuperación.

-Supera la brecha de habilidades: Brinda información accesible para distintos equipos sin necesidad de que todos sean expertos en cada área técnica.

-Visión unificada: Proporciona una sola plataforma de observación para desarrolladores, DevOps y equipos de seguridad, evitando múltiples herramientas separadas.

-Mejora de procesos: Fomenta prácticas como desarrollo orientado a pruebas, mayor seguridad y monitoreo estandarizado en la infraestructura.

## 3. Defina

- **Métricas**:

Son datos numéricos, generalmente en series de tiempo, que permiten medir, calcular o promediar el desempeño de componentes de infraestructura como servidores, routers o firewalls, o de aplicaciones como bases de datos, web servers, middleware, etc. Sirven para detectar tendencias y anomalías, aunque por sí solas no muestran todo el panorama cuando ocurre un fallo.

- **Logs y eventos**:

Los eventos son todo lo que ocurre en la pila de una aplicación, y los logs son registros detallados y con sello de tiempo de esos eventos. Incluyen mensajes de diferentes capas como API, microservicio, contenedor, sistema operativo, red, base de datos, y contienen metadatos valiosos. Para obtener observabilidad completa, los logs de cada componente deben recopilarse y correlacionarse con el evento.

- **Traces**:

Son el registro del recorrido completo de una transacción en una arquitectura distribuida. Muestran cada llamada entre componentes (microservicios u otros), los puntos de interacción, los tiempos de ejecución y la latencia en cada paso, ya sea en procesos iniciados por usuarios  o por la aplicación misma.

 <br>

## 4. Comente las mejores prácticas prácticas de Observabilidad

Las mejores prácticas de observabilidad son:

-Etiquetado de recursos: Definir un conjunto de tags comunes como nombre, propósito, versión, grupo responsable y región para cada recurso.

-Recolección de métricas: Obtener la mayor cantidad de métricas posibles de todos los componentes con valores detallados y granulares.

-Procesamiento de métricas: Agrupar, promediar o generar percentiles y definir umbrales que marquen el comportamiento normal del sistema.

-Gestión de logs: Habilitar el registro en todos los componentes, incluidos SaaS o servicios externos, asegurando que cada log contenga metadatos comunes por ejemplo fecha/hora, usuario, IP origen/destino, servicio, función, tipo y severidad del evento. Evitar recopilar mensajes de depuración innecesarios.

-Instrumentación y trazas: Instrumentar el código para obtener trazas que registren funciones llamadas, tiempos de ejecución, errores y metadatos adicionales.

-Identificación de transacciones clave: Mapear los flujos críticos como el login, carrito de compras, comparación de precios a los componentes que los soportan.

-Alertas bien definidas: Configurar alertas con alcance claro basadas en métricas, logs, monitoreo sintético o RUM, como velocidad de carga de página o uso de CPU.

## 5. Explique en que consiste un APM

APM significa Application Performance Monitoring o Application Performance Management, y aunque ambos conceptos se relacionan, tienen diferencias.

Application Performance Monitoring se centra en medir el rendimiento de una aplicación o sitio web a través de métricas como uso de CPU, memoria, red, base de datos, número de visitantes, velocidad de carga y disponibilidad. Su propósito es recolectar datos y alertar cuando se salen de los valores esperados.

Application Performance Management, en cambio, va más allá: analiza de forma continua la experiencia del usuario final, el rendimiento, la disponibilidad, los patrones de uso y las dependencias de los componentes. Su objetivo es detectar anomalías, identificar causas raíz y responder al por qué, cuándo y dónde ocurren los problemas.

En el contexto de observabilidad, APM es clave porque ayuda a tener visibilidad completa del sistema. Para lograrlo, una solución APM debe incluir:

-Visibilidad de la infraestructura.

-Monitoreo de transacciones.

-Trazabilidad de transacciones distribuidas.

-Monitoreo de la experiencia del usuario y pruebas sintéticas.

-Mapas de servicios.

-Analítica de datos.
