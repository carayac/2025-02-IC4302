# AuroraDB

## 1. Explique los conceptos de HA y DR

Alta disponibilidad (HA) se refiere a la capacidad de una base de datos para mantener un rendimiento operativo incluso ante fallas de hardware, software o red, con poca o ninguna intervención manual. Esto se logra mediante la creación de réplicas del sistema principal en hardware independiente, que pueden asumir el rol principal en caso de interrupciones, utilizando mecanismos como redirección DNS, IP virtual o proxies.

Por otro lado, recuperación ante desastres (DR) es el conjunto de procedimientos que permiten restaurar el acceso y la funcionalidad del sistema después de un desastre natural o humano. Incluye estrategias de respaldo y puede requerir acciones manuales, como ejecutar scripts o mover operaciones a otra región no afectada, garantizando así la continuidad del servicio.

## 2. Explique los conceptos de RPO y RTO

RPO (Recovery Point Objective) es el tiempo máximo aceptable desde el último punto de recuperación de datos. Define cuánto dato puede perderse entre el momento de una interrupción y la última copia disponible; por ejemplo, un RPO de 15 minutos implica que se podrían perder hasta 15 minutos de información.

RTO (Recovery Time Objective) es el tiempo máximo aceptable que puede transcurrir entre una interrupción y la restauración del servicio. Indica cuánto tiempo puede permanecer inactiva la base de datos; por ejemplo, un RTO de 5 minutos significa que el sistema debe recuperarse completamente en ese plazo.


## 3. ¿Como funciona la arquitectura de AuroraDB

La arquitectura de AuroraDB separa el cómputo del almacenamiento, permitiendo que ambos se recuperen de forma independiente ante fallos. Ofrece configuraciones Single-AZ o Multi-AZ para mejorar la disponibilidad y realiza copias de seguridad automáticas con posibilidad de restaurar a un punto en el tiempo.

Además, con Aurora Global Database, los datos se replican asíncronamente entre regiones con baja latencia, lo que permite lecturas rápidas y recuperación ante desastres en menos de un minuto, garantizando alta disponibilidad y continuidad global.