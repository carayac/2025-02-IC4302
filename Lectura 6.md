# Cassandra

## 1. Explique la arquitectura de Cassandra 

La arquitectura de Cassandra es distribuida y de tipo peer-to-peer, donde todos los nodos son iguales y se comunican mediante un protocolo gossip, sin depender de un nodo maestro. Esta estructura permite alta escalabilidad, rendimiento y disponibilidad continua, ya que evita puntos únicos de falla y puede manejar grandes volúmenes de datos y miles de operaciones concurrentes incluso en varios centros de datos.

## 2. Como funciona la replicación de Cassandra? Como se diferencia de un esquema Master-Slave?

La replicación en Cassandra funciona de forma automática y distribuida entre todos los nodos del clúster, que forman un “anillo” o ring. No existe un nodo principal; todos los nodos son iguales y pueden recibir lecturas o escrituras. Los datos se particionan y replican de manera transparente, guardando copias redundantes en diferentes nodos (incluso en distintos racks o centros de datos) para asegurar alta disponibilidad y tolerancia a fallos.

A diferencia del esquema Master-Slave, Cassandra no depende de un nodo maestro que coordine las operaciones. En su lugar, utiliza una arquitectura peer-to-peer y un protocolo gossip para la comunicación entre nodos, eliminando el punto único de falla y permitiendo una replicación más sencilla, escalable y continua.

## 3. Como afecta el modelo de replicación y de escritura la consistencia de datos?

El modelo de replicación y escritura de Cassandra permite escribir y leer datos desde cualquier nodo del clúster, lo que brinda alta disponibilidad y tolerancia a fallos, pero reduce la consistencia inmediata. Cuando un nodo falla, los datos se escriben temporalmente en otro y luego se sincronizan al recuperarse, lo que garantiza durabilidad y recuperación automática, aunque puede haber retrasos en la actualización entre nodos. Cassandra cumple con la atomicidad, aislamiento y durabilidad (AID), pero no con la consistencia estricta de las bases de datos ACID tradicionales.