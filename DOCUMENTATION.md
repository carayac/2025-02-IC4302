# Proyecto Opcional - Crossref Search

**Curso:** IC4302 - Bases de Datos II  
**Institución:** Tecnológico de Costa Rica  
**Escuela:** Ingeniería en Computación  
**Semestre:** Segundo Semestre 2025  

---
## Contenido
-> [Introducción](#1-introducción)  
  
-> [Objetivos](#2-objetivos)  
  
-> [Arquitectura del Sistema](#3-arquitectura-del-sistema)  
  
-> [Instrucciones de ejecución](#4-instrucciones-de-ejecución)  
  
-> [Pruebas Unitarias y Resultados](#5-pruebas-unitarias-y-resultados)  
  
-> [Pruebas Funcionales y Resultados](#6-pruebas-funcionales-y-resultados)  
  
-> [Conclusiones y Recomendaciones](#7-conclusiones-y-recomendaciones)  

-> [Referencias](#8-referencias)  
  


## 1. Introducción  
<details>
  <summary>Desplegar información</summary>
  
Este documento describe el desarrollo e implementación del proyecto **Crossref Search**, cuyo propósito es generar ciertos pasos en cadena, ejecutarlos en diferentes maquinas y así obtener un gran volumen  de datos; todo esto basado en microservicios desplegados en Docker, Kubernetes y Helms.  Crossref search integra tres componentes principales: un **web-spider** que se encarga de consultar a la API de Pubmed para conseguir ciertos identificadores de articulos y así generar jobs; un **downloader** que descarga los metadatos, consulta a la API de Crossref los documentos JSON con la información pertinente de cada artículo y finalmente se implementa un **spark-job** que procesa los archivos almacenados y realiza transformaciones utilizando en campos de fecha, autores y referencias utilizando Spark SQL.  
  
---
</details>

## 2. Objetivos

<details>
  <summary>Desplegar información</summary>

### 2.1 General
Desarrollar competencias en el uso de tecnologías y lenguajes de programación que se emplearán durante el curso.

### 2.2 Específicos
- Implementar un web crawler en **Python**.  
- Procesar datos utilizando **Spark SQL**.  
- Implementar una **base de datos** para la búsqueda de artículos científicos.  
- Automatizar la solución con **Docker, Docker Compose, Kubernetes y Helm Charts**.  
- Desarrollar arquitecturas basadas en **microservicios sobre Kubernetes**.  
- Instalar y configurar **bases de datos relacionales y NoSQL**.  

---
</details>
  
## 3. Arquitectura del Sistema

<details>
  <summary>Desplegar información</summary>
  
El sistema está compuesto por los siguientes servicios:

**Web Spider**  
Este componente es el encargado de inciciar el flujo del sistema, se ejecuta periódicamente (cada 12 horas) y consulta la API de *PubMed* para obtener artículos cientificos. Seguidamente, organiza los resultados en *jobs* que incluyen los identificadores de los artículos encontrados, los almacena en *MariaDB* y publica el `job_id` en RabbitMQ para que pueda ser utilizado posteriormente.
  
**Downloader**  
El dowloader funciona como un consumidor activo de RabbitMQ. Cuando recibe un `job_id`, actualiza su estado en MariaDB a *in-progress*, obtiene los datos básicos de PubMed incluyendo incluyendo el DOI y consulta la API de *Crossref* con ese mismo DOI obtenido. El resultado se guarda como archivos JSON en un *PVC (Persistent Volume Claim)*.  
  
**Spark Job**  
Una vez el dowloader termine su ejecución, el spark-job procesa todos los JSON generados para realizar transaformaciones utilizando *Apache Spark SQL* como las siguientes:  
  - Normalización de fechas (`created.date` y `indexed.date`).  
  - Creación de una lista de autores con formato `"apellido, nombre"`.  
  - Extracción de títulos de referencias que contienen DOI.  
  Una vez las transformaciones se hayan ejecutado, los documentos se envían a un índice en *Elasticsearch* llamado data, para que posteriormente sean consultados mediante *Kibana*.
  
Dentro de la infraestructura de soporte dentro del sistema se encuentran:  
  
**RabbitMQ**  
Es el sistema que sirve como intermediario para que los servicios se pasen mensajes y realizar sus funciones correspondientes. Permite que el Web Spider y el Downloader trabajen de forma asíncrona, equilibrada en caso de que haya más de un dowloader y soportando reinicio en caso de que algun mensaje no se procese.
  
**MariaDB**  
Es la base de datos relacional utilizada para registrar los *jobs*, sus estados, fechas de inicio y fin, y la lista de artículos omitidos que son los que no pudieron procesarse.  
  
**Elasticsearch**  
Es el sistema que se encarga de la busqueda y el analisis que almacena los datos procesados por el spark y permite consultas y filtros sobre los componenetes de los json una vez los docs queden indexados
  
**Kibana**  
Es la interfaz gráfica utilizada para desplegar y consultar los datos y transformaciones procesados por Elasticsearch.

---
</details>

## 4. Instrucciones de Ejecución
  
<details>
  <summary>Desplegar información</summary>  
  
### 4.1 Requisitos Previos
- Cuenta en Docker Hub
- Docker y Docker Compose  
- Kubernetes (Minikube o Docker Desktop)  
- Helm Charts instalados  
- Git
- Lens

### 4.2 Instalación de Componentes  


#### 1. Descargue el repositorio del proyecto en su computadora 
  
   ```bash
   git clone <URL_REPO>
   ```

Después ingrese a la carpeta del repositorio por medio de la terminal bash:  

   ```
cd 2025-02-IC4302
   ```
  
#### 2. Construya la imagenes de docker
Para poder realizar la construcción de las imágenes Docker. debe ingresar a la carpeta **docker** desde una terminal Bash y ejecutar el siguiente comando: 

 ```
./build.sh usuario 
 ```  
  
> NOTA: 
> Sustituya la palabra ususario con su usario de Docker Hub

#### 3. Configure el registro de  las imágenes para el chart
En su proyecto, ingrese a la carpeta de charts **-->** application **-->** values.yaml y reemplace el resgistro de docker por su usuario correspondiente en docker hub:  
  
 ```
config:
  docker_registry: usuario
 ```

#### 4. Instale el Helm Chart del proyecto  

En su proyecto, ingrese a la carpeta de **charts** desde una terminal Bash y ejecute el siguiente comando:  
    
 ```
./install.sh
 ```

#### 5. Desinstalación del Helm Chart del proyecto

En caso de que usted necesite hacer la desinstalación del helm chart, ingrese a la carpeta de **charts** desde una terminal Bash y ejecute el siguiente comando:  
    
 ```
./uninstall.sh
 ```
> NOTA: 
> Si no necesita la instalación, ignore este paso
  
#### 6. Accese a los pod

Para verificar que su instalación se ejecutó correctamente puede ejecutar el siguiente comando desde la terminal Bash:  
    
 ```
kubectl get pods
 ```
O también puede ingresar a la aplicación de **Lens** y dirigirse a la sección de **Workloads --> Pods** y verifique que estos tengan un estado de *Running*

![](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/estado%20running.png)  

#### 7. Inicie el flujo del web-spider

Después de ejecutar los pasos anteriores, el web.spider está definido como un CronJob en Kubernetes el cual se ejecuta cada 12 horas.  Para poder ejecutar su flujo sin esperar su horario programado debe dirigirse a **Workloads --> Cron Jobs** y seleccionar el web-spider y usar la opción "Trigger" para ejecutar el job de inmediato.  

![](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/cronJob.png)

Una vez realizado este paso, puede dirigirse a la sección de **Pods** y esperar a que el web-spider cambie su estado a Succeed, lo que significará que ha terminado su ejecución.  

#### 8. Inicie el flujo del spark-job

Después de que la ejecución del web-spider ha terminado, puede empezar el flujo del spark-job de la misma forma.  
El spark job está definido como un CronJob en Kubernetes el cual se ejecuta cada 12 horas.  Para poder ejecutar su flujo sin esperar su horario programado debe dirigirse a **Workloads --> Cron Jobs** y seleccionar el spark-job y usar la opción "Trigger" para ejecutar el job de inmediato.  

![](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/cronJob.png)

Una vez realizado este paso, puede dirigirse a la sección de **Pods** y esperar a que el spark-job cambie su estado a Succeed, lo que significará que ha terminado su ejecución.  

#### 9. Acceda a Kibana para consultar los datos y transformaciones  
  
Una vez que el **spark-job** haya terminado su ejecución y el pod cambie su estado a **Succeed**, los datos ya estarán disponibles en **Elasticsearch** y podrán consultarse mediante **Kibana**.  
Para ingresar a Kibana:  
- Ingrese a **Network --> Services**. y seleccione el serivio llamado `ic4302-kb-http`
- Seleccione la opción **Port Forward** para exponer el servicio en su máquina local.  Inmediatamente se abrirá un enlace en su navegador para poder ingresar a la pagina de inicio.
![](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/kibana.png)  
- Ingrese los datos de inicio de sesión
 ```
User: `elastic`
Password:** debe obtenerse desde Lens:
 ```
- Para obetner la contraseña, debe ingresar a **Config --> Secrets**, seleccionar `ic4302-es-elastic-user` y copie el valor de la contraseña y peguelo en el inicio de sesión.
![](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/secret.png)

Una vez haya completado estos pasos, puede crear consultas para ver los documentos almacenados y verificar los nuevos campos.  
  
---
</details>

## 5. Pruebas Unitarias y Resultados

<details>
  <summary>Desplegar información</summary>

### Web-Spider  
<details>
  <summary>Desplegar información</summary>
  
- Extracción de count de API de Pubmed ![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/pruebas_pubmed_web-spider.png)
- Obtener lista de ids de API de Pubmed ![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/pruebas_pubmed_web-spider.png)
- Inicializar job con los campos correctos ![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/pruebas_pubmed_web-spider.png)
- Insertar job en MariaDB ![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/pruebas_MariaDB_web-spider.png)
- Enviar job_id por RabbitMQ ![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/pruebas_RabbitMQ_web-spider.png)

</details>

### Downloader  
<details>
  <summary>Desplegar información</summary>

- Conexión a MariaDB 
![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/Prueba1-downloader.jpg)
- Actualización del estado del job 
![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/Prueba2-downloader.jpg)
- Actualización del end date del job 
![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/Prueba3-downloader.jpg)
- Obtener los IDs del job 
![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/Prueba4-downloader.jpg)
- Obtiene respuesta válida de Pubmed 
![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/Prueba5-downloader.jpg)
- Extrae correctamente los DOIs 
![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/Prueba6-downloader.jpg)
- Procesa correctamente los DOIs 
![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/Prueba7-downloader.jpg)
- Guarda correctamente el JSON 
![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/Prueba8-downloader.jpg)
- Funciona correctamente el Crossref 
![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/Prueba9-downloader.jpg)
</details>

### Spark-Job  
<details>
  <summary>Desplegar información</summary>

#### Transformación 1 – Fechas  
La transfromación de fechas consiste en cambiar los campos de la columna message `indexed.date-time` y `created.date-time` al formato **MM-DD-YYYY**, y guardar los cambios en un nuevo campo llamado `indexed.date` y `reated.date` en la columna message  
- **Objetivo de la prueba:** Validar que se extraen correctamente las fechas `created` e `indexed` y que se formatean correctamente.  
- **Condición:** La pruba se basa en el documento JSON con el DOI = `10.1126/science.adz6436`  
- **Salida esperada:**
```json
"indexed": {
  "date": "08-02-2025"
}, 
"created": {
  "date": "08-01-2025"
 ```

**Salidas en caso de fallar:**

Test falló: La fecha 'indexed.date' no coincide con el valor esperado
Test falló: La fecha 'created.date' no coincide con el valor esperado


#### Transformación 2 – Autores  
La transformacion de autores agrega un nuevo campo en la columna message `autor_names` que contiene una lista de los autores del artículo en el formato **"Apellido, Nombre"**, construido a partir de los campos `author.family` y `author.given` ambos de la columna message tambien.  
- **Objetivo de la prueba:** Validar que se extraen correctamente todos los autores en `autor_names` con el formato que corresponde.  
- **Condición:** La pruba se basa en el documento JSON con el DOI = `10.1126/science.adz6436`  
- **Salida esperada:**  
```json
"autor_names": ["Permar, Sallie R.", "Wilson, Patrick C."]
```

**Salidas en caso de fallar:**
Test falló: La lista de 'autor_names' no coincide con el valor esperado


#### Transformación 3 – Referencias  
La transformación de referencias consiste en agregar un nuevo campo en la columna message llamada `reference_tittle` que contenga una lista de los títulos de los artículos referenciados, tomando como base el campo `reference` tambien de la columna message, siempre y cuando estas referencias contengan un DOI.  Si una referencia no tiene DOI es ignorada, de lo contrario se agrega el campo.  
- **Objetivo de la prueba:** Validar que los todos los títulos referenciados se extraen correctamente.
- **Condición:** La pruba se basa en el documento JSON con el DOIorg = `10.1126/science.adz6436`
- **Salida esperada:**
 ```json
  "reference_tittle": ["Strategies for HIV-1 vaccines that induce broadly neutralizing antibodies",
  "Precise targeting of HIV broadly neutralizing antibody precursors in humans",
  "Vaccination with mRNA-encoded nanoparticles drives early maturation of HIV bnAb precursors in humans"]
```


**Salidas en caso de fallar:**
Test falló: La lista de 'message.reference_tittle' no coincide con el valor esperado


</details>  

---

</details>

## 6. Pruebas Funcionales y Resultados

<details>
  <summary>Desplegar información</summary>


- ### 5.2 Pruebas Funcionales

A continuación, se adjunta un video donde se demuestra que el proyecto cumple con todas las funcionalidades, donde especificamente demuestra las siguientes:

- Verificar que los *jobs* se crean en MariaDB.  
- Verificar que los *jobs-id* se envían a través del canal de RabbitMQ.
- Comprobar que los documentos se guardan en JSON.  
- Confirmar que Elasticsearch contiene los documentos procesados.  
- Visualizar en Kibana los resultados.  

[Video de Demostración](PO/images/Video.mkv)

---
</details>

## 7. Conclusiones y Recomendaciones
<details>
  <summary>Desplegar información</summary>

### 7.1 Conclusiones
1. El proyecto logró que uno aprendiera bastante a como manejar la automatización de procesos mediante las variables de entorno y Kubernetes. Esto es muy valioso de aprender para seguir practicándolo en proyectos futuros, con el fin de mejorar su eficiencia, escalabilidad y profesionalismo.
2. RabbitMQ demostró ser una herramienta de gran ayuda, ya que facilita la comunicación de sistemas de manera automática. Lo cual es bastante eficiente y útil para este tipo de proyectos.
3. El uso de la herramienta SparkSQL permite desarrollar un estilo de programacion simplificado, ya que facilita el manejo de datos usando consultas SQL familiares sin necesidad de escribir mucho código en APIs más verbosas.
4. Los contenedores permiten integrar múltiples tecnologías dentro de un mismo proyecto de manera flexible y portable. En conjunto con Helm Charts, se facilita la instalación, gestión y despliegue de aplicaciones, lo que representa un interesante avance hacia la automatización.
5. Además, los contenedores de Kubernetes proporcionan un entorno aislado, permitiendo que diferentes componentes funcionen de manera independiente, garantizando la estabilidad del software. Esto también facilita las pruebas y desarrollo en paralelo para programas de gran tamaño.
6. El sistema de gestión de MariaDB fue muy útil a la hora de volúmenes grandes de datos por medio de procesos de paginación, y permite almacenar datos de manera estructurada y consistente, lo que resulta fundamental para cualquier proyecto de software a nivel profesional.
7. El uso de cron jobs en Kubernetes es sumamente util porque permite la ejecución periodica de los procesos así como su testeo o ejecución en caso de que no se quiera esperar al horario programado.
8. Kibana representó una herramienta de gran valor al proyecto pues por medio de ella puede visualizarse los resultados de todas las tranformaciones haciendo el sistema y su objetivo principal mucho más comprensibles.
9. El uso de Kubernetes y contenedores fue muy util para conocer más sobre la escalabilidad en en los proyectos de software, porque permite añadir más réplicas de un servicio. Como por ejemplo con los dowloaders que permite manejar varios a la vez dependiendo la carga que necesite procesarse.
10. El uso de volúmenes persistentes en Kubernetes fue bastatnte útil para compartir datos entre todos los serivicios del sistema y asi poder accesar a cualquier documento dentro estos dervicios.
11. El tener dispositivos con distintos sistemas operativos genera complicaciones a la hora de unificar. Por ejemplo, a la hora de correr una máquina virtual de windows en una computadora mac, los permisos de virtualización van a generar problemas constantes al correr Docker Desktop.
12. En general, el proyecto fue muy util para comprender conceptos y obetener experiencia en prácticas de big data y data engineering modernas y que son utilizadas frecuentemente en el mercado, así como para la preparación para proyectos futuros que sean más grandes y complejos.

### 7.2 Recomendaciones
1. Siempre implementar prints mediante los procesos, de manera que se puede seguir todo paso a paso y ver los resultados que están dando las funciones para verificar si son correctos 
2. Todas las funciones manejarlas con try y errores, ya que es muy útil para reconocer el fallo en específico a la hora de hacer las pruebas, además facilita mucho el proceso de correcciones  
3. El uso de variables de entorno permiten separar la configuración del código, lo que facilita su mantenimiento, y aumenta la portabilidad entre distintos entornos y reduce la complejidad al realizar cambios o actualizaciones en este caso fue de utilidad para rutas y credenciales.
4. Se recomienda investigar previamente las tecnologías poco conocidas o con limitada comprensión, ya que esto facilita su aplicación en el desarrollo de proyectos, mejora la comprensión de su funcionamiento y agiliza la solución de errores.
5. Es recomendable probar los distintos componentes del software por separado antes de integrarlos, para poder detectar problemas específicos antes de que afecten todo el sistema. 
6. Hacer un control de versiones y documentar los cambios en el código, usando herramientas como GitHub, para facilitar la colaboración en equipo y la recuperación y restauración del código anterior en caso de  errores accidentales.
7. Realizar una limpieza del Persistent Volume Claim utilizado después de realizar la desinstalación de los charts o antes de su instalación, esto con el objetivo de prevenir posibles errores a la hora de ejecutar los 3 componentes principales.
8. Realizar pruebas automatizadas o unitarias a cada uno de los componenetes principales antes de desplegar en kubernetes para reducir errores.
9. Establecer code reviews semanales con el equipo para mejorar la calidad del código, para compartir conocimientos adquiridos durante el desarrollo de componentes o bien para detectar errores y no esperar hasta la integración final del proyecto.
10. Utilizar los dispositivos en su sistema operativo original y buscar que todo el equipo tenga el mismo sistema operativo para facilitar la cohesión de los distintos avances.
11. Implementar documentación interna dentro del código donde se especifique descripcion, entradas y salidas del programa para una mejor comprensión

---
</details>

## 8. Referencias

<details>
  <summary>Desplegar información</summary>

- [Apache Spark](https://spark.apache.org/)  
- [Crossref API](https://api.crossref.org)  
- [PubMed API](https://eutils.ncbi.nlm.nih.gov/)  
- [Kubernetes Documentation](https://kubernetes.io/)  
- [Docker Documentation](https://docs.docker.com/)  
- [Funciones de PySpark](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.Column.dropFields.html)
- [Volumenes](https://kubernetes.io/docs/concepts/storage/volumes/)
- [Dev Tool Kibana+Elastic](https://www.elastic.co/docs/explore-analyze/query-filter/tools/console)
- [Apache Spark Support](https://www.elastic.co/docs/reference/elasticsearch-hadoop/apache-spark-support)
- [Upsert-ElasticSearch](https://stackoverflow.com/questions/50962579/spark-dataframe-upsert-to-elasticsearch)
- [Requests Documentation](https://docs.python-requests.org/en/latest/index.html)
- [UUID Documentation](https://docs.python.org/es/3/library/uuid.html)
- [MariaDB / Python](https://mariadb.com/docs/connectors/connectors-quickstart-guides/connector-python-guide)
- [Kubernetes CronJob](https://kubernetes.io/docs/tasks/job/automated-tasks-with-cron-jobs/)
- [Unittest MagicMock](https://docs.python.org/3/library/unittest.mock.html#magic-mock)
- [Pytest](https://docs.pytest.org/en/stable/getting-started.html)
- [Mock DBs](https://medium.com/@prasanna44.palivela/python-unittest-framework-how-to-mock-db-and-apis-5f8ca2baf2b2)
- [Scala Test](https://www.scalatest.org/user_guide/using_assertions)
- [Http Status Codes] (https://developer.mozilla.org/es/docs/Web/HTTP/Reference/Status)


---
</details>
