Bases de Datos II
Helena Vargas
II Sem 2025
# Lectura 6: Apache Cassandra

## Explique la arquitectura de Cassandra
Tiene una arquitectura distribuida y permite un gran desempeño a velocidades extremas. Es una base NO-SQL masivamente escalable. Se construyó pensando que el hardware y los sistemas vana  fallar. Por lo tanto, se utiliza un camino diferente para manejar y proteger la información. 

Cassandra tiene una arquitectura de "igual a igual". No hay un nodo maestro y todos los nodos se comunican por "protocolos de chisme". Construida por arquitectura de escala, quiere decir que es capaz de manejar PetaBytes de información y cantidades de usuarios por segundo. Provee distribución automática a través de los nodos que participan en un anillo de datos. La información se reparte a través de los nodos de manera al azar o de modo ordenado. Es más común que sea aleatorio.


## ¿Cómo funciona la replicación de Cassandra? ¿Cómo se diferencia de un esquema Master-Slave?
La replicación es incorporada y personalizada. Almacena redundancias de datos en los nodos que forman parte del anillo. Esto significa que si un nodo se cae, uno o más copias de los datos siguen disponibles en otra máquina del grupo. 

A diferencia de un esquema master-slave, es más fácil de configurar. El desarrollador solo debe especificar cuantas copias de datos requiere y Cassandra hace el resto. También permite que los datos se guarden automáticamente en racks físicos, múltiples centros de datos y plataformas en la nube.

## ¿Cómo afecta el modelo de replicación y de escritura la consistencia de datos?

Cualquier nodo del grupo puede ser leído o escrito, por lo que se lee/escribe en cualquier lugar. Cuando los datos son escritos, primero se escribe un registro de compromiso para asegurar datos completos, seguros y duraderos. Los datos se escriben en una estructura en memoria llamada memtable que luego se vacía en un disco llamado sstable. Cassandra ofrece datos sincronizados a través de los grupos de bases de datos. Un desarrollador puede decidir qué tan consistentes deben ser los datos. La sincronización de los datos es soportada a través de uno o varios centros de datos.
