# Apuntes de Clase

## Storage

- **Raid Controller**: nos permite mejorar la redundancia y  distribuir los datos entre los discos para mejorar el rendimiento

- **Uso de discos mecanicos**: se tiene un eje con varios platos, los cuales tienen caras y estos tienen tracks. La cabeza lectora se coloca en un track especifico, donde al rotar el segmento, extrae informacion

![1757402390338](image/Apuntes2/1757402390338.png)

(No es recomendable cuando se tiene que mover la cabeza lectora constantemente para realizar queries)

- **Configuración espejo**: consiste en que se duplica los datos en dos discos. Es una estrategia de redundancia, si uno falla, el otro sigue funcionando sin pérdida de datos

Existen 6 tipos de Raid, los cuales con:

- **Raid 0**: pasa un archivo por striping, donde distribuye los stripes en discos. De esta manera incrementa el storage y speed read y writes, pero decrementa el data availability

![1757402114123](image/Apuntes2/1757402114123.png)

- **Raid 1**: utiliza la configuración de espejo, donde escribe los strips en ambos discos. Asi aumenta el data availability, pero decrementa el rendimiento

![1757402150198](image/Apuntes2/1757402150198.png)

- **Raid 2**: utiliza bits de pariedad, que es una tecnica donde si la cantidad de bits en la cadena es par se agrega un 0 al final, si esta es impar se agrega un 1 Con este metodo si se pierde un disco, se puede recuperar. Parte los strips en bits y los reparte en cada disco, de esta manera se pueden perder hasta dos discos sin problema

![1757402184432](image/Apuntes2/1757402184432.png)

- **Raid 3**: practicamente usa la misma estrategia que el Raid 2, pero se diferencian que en este se usan bytes en lugar de bites

![1757402434621](image/Apuntes2/1757402434621.png)

- **Raid 4**:  utiliza striping para distribuir los datos en bloques entre los discos, pero reserva uno exclusivamente para almacenar la pariedad. Esta pariedad permite recuperar la información si se pierde un disco. 

![1757402471900](image/Apuntes2/1757402471900.png)

- **Raid 5**: distribuye los bloques de datos entre todos los discos usando striping, y en lugar de usar bits de pariedad simples, aplica operaciones XOR para calcular la pariedad. Esta pariedad también se distribuye entre los discos, evitando que uno solo se sobrecargue. Si se pierde un disco, los datos se pueden reconstruir con los bloques restantes y la pariedad.

![1757402246569](image/Apuntes2/1757402246569.png)

- **Raid 6**: sigue el mismo principio que el Raid 5, pero en lugar de una sola pariedad, utiliza dos capas de pariedad distribuidas. Esto permite que hasta dos discos fallen sin perder la información.

En la actualidad, ya no se suele configurar esto, sino que se usa Nas o San:

- **NAS**: es un dispositivo de almacenamiento conectado a la red local. Funciona como un servidor de archivos, donde los usuarios acceden a los datos por protocolos como SMB o NFS. El NAS tiene su propio sistema operativo y gestiona los archivos directamente. Se comunica por Ethernet y trabaja a nivel de archivo, lo que lo hace ideal para compartir documentos, multimedia o respaldos. No requiere configuración RAID manual, ya que el sistema lo gestiona internamente. Es más usado en oficinas pequeñas o entornos domésticos.

- **SAN (storage area networks)**: es una red dedicada exclusivamente al almacenamiento. Conecta servidores y dispositivos de almacenamiento por medio de switches y protocolos como Fibre Channel o iSCSI. A diferencia del NAS, trabaja a nivel de bloque, lo que permite que los servidores vean los discos como si fueran locales. Esto mejora el rendimiento y la escalabilidad, siendo ideal para centros de datos, virtualización y bases de datos de alto rendimiento. La configuración es más compleja, pero permite redundancia, alta disponibilidad y recuperación ante fallos.

- **Raw data**: son los datos en la forma del sistema que los estamos recuperando.

- **Batch**: es la cantidad de datos que procesa el sistema, se sabe cuando entran y terminan, suelen estar en rest

- **Streaming**: es la cantidad de datos que procesa el sitema al igual que el batch, pero no se sabe cuando terminan. Estos suelen estar en transit o on the fly.

- **IoT**: Significa Internet of Things. Es una red de dispositivos físicos que están conectados entre sí y al internet, capaces de recolectar, enviar y procesar datos. Estos dispositivos pueden ser sensores, actuadores, cámaras, relojes, etc. Los datos que generan están en constante flujo, por lo que se procesan en tiempo. Estos no se pueden trabajar con DB SQL o no SQL, ya que generan demasiados eventos.

- **Apache Kafka**: es una plataforma de mensajeria, donde no usan discos y tienen todo en memoria.  Expone un buffer grande donde se obtienen mensajes por medio de un producer que es el que los envia, y los recibe un consumer que es el que los procesa

- **ETL**: significa Extract, Transform, Load. Es un proceso que se utiliza para mover datos desde una o varias fuentes hacia un sistema de destino, como una base de datos o un data warehouse. Primero se extraen los datos en su forma original, luego se transforman aplicando reglas de negocio, limpieza o reestructuración, y finalmente se cargan en el sistema destino de forma organizada y lista para análisis.

- **Window**: es una técnica que permite analizar una porción específica de datos dentro de un conjunto más grande. Se define un rango fijo, como lo puede ser por tiempo o por datos. Esta ventana sirve para medir la velocidad y realizar operaciones.

- **Sliding window**: es una técnica donde la ventana se mueve progresivamente sobre el conjunto de datos. A medida que entran nuevos elementos, los más antiguos salen de la ventana. Esto permite procesar datos en tiempo real o en flujos continuos sin recalcular todo desde cero.

![1757402573613](image/Apuntes2/1757402573613.png)

- **Apache Beam**: es un framework distribuido para construir pipelines de procesamiento de datos en batch y streaming. 

- **Data Warehouse**: es un sistema centralizado que almacena grandes volúmenes de datos estructurados provenientes de múltiples fuentes. Su objetivo es facilitar el análisis, la toma de decisiones y la generación de reportes. 




