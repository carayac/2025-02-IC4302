# Spanner

## 1. ¿Cómo funciona la arquitectura de Spanner?

La arquitectura de Spanner se basa en una base de datos escalable y globalmente distribuida, que divide (shardea) los datos en múltiples máquinas de estado Paxos ubicadas en distintos centros de datos alrededor del mundo

Utiliza replicación para garantizar alta disponibilidad y baja latencia, permitiendo que los clientes cambien automáticamente entre réplicas si ocurre un fallo.
El sistema puede reconfigurar y migrar datos automáticamente entre servidores y centros de datos para balancear la carga y mantener el rendimiento.
Además, Spanner ofrece un modelo semirrelacional con soporte para transacciones y consultas SQL, lo que combina la escalabilidad de sistemas NoSQL con las ventajas estructuradas de una base de datos relacional

## 2. ¿Cómo multi versionamiento en Spanner?

Spanner implementa un modelo multiversión temporal, donde cada dato almacenado tiene múltiples versiones.
Cada versión se marca automáticamente con una marca de tiempo de confirmación (commit time), lo que permite a las aplicaciones acceder a versiones anteriores de los datos.
Las versiones antiguas se eliminan según políticas de recolección de basura configurables, manteniendo la eficiencia del sistema

Este enfoque permite lecturas históricas y garantiza consistencia temporal y transaccional incluso en un entorno distribuido globalmente

## 3. ¿En qué consiste el TRUETIME?

El TrueTime es una API creada por Google que proporciona una noción de tiempo con margen de error controlado. En lugar de devolver una sola marca de tiempo (como lo hace el tiempo estándar), devuelve un intervalo de tiempo (TTinterval) que indica entre qué dos valores se encuentra el tiempo real.

TrueTime se basa en relojes atómicos y GPS distribuidos en varios servidores maestros dentro de cada centro de datos. Estos se sincronizan constantemente entre sí y estiman la incertidumbre del tiempo, lo que permite garantizar que todos los servidores tengan una visión coherente y verificable del tiempo, incluso ante fallos o variaciones en los relojes.



