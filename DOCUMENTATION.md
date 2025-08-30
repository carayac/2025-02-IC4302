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
  
-> [Pruebas](#5-pruebas)  
  
-> [Resultados](#6-resultados)  
  
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

- **Web Spider (Python, Kubernetes CronJob):** consulta periódicamente PubMed y organiza los artículos en *jobs*.  
- **Downloader (Python, Kubernetes Deployment):** recibe los *jobs*, descarga metadatos desde PubMed y Crossref, y guarda los resultados en JSON.  
- **Spark Job (Scala, Kubernetes CronJob):** procesa los datos, realiza transformaciones con Spark SQL y los indexa en Elasticsearch.  

Los servicios se comunican mediante **RabbitMQ**, y los datos son almacenados en **MariaDB** y **Elasticsearch**, permitiendo su consulta a través de **Kibana**.

---
</details>

## 4. Instrucciones de Ejecución
  
<details>
  <summary>Desplegar información</summary>  
  
### 4.1 Requisitos Previos
- Docker y Docker Compose  
- Kubernetes (Minikube o Docker Desktop)  
- Helm Charts instalados  
- Git  

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

> NOTA: 
> IMAGEN  

#### 7. Inicie el flujo del web-spider

Después de ejecutar los pasos anteriores, el web.spider está definido como un CronJob en Kubernetes.  Para poder ejecutar su flujo sin esperar su horario programado debe dirigirse a **Workloads --> Cron Jobs** y seleccionar el web-spider y usar la opción "Trigger" para ejecutar el job de inmediato.  

> NOTA: 
> IMAGEN

Una vez realizado este paso, puede dirigirse a la sección de **Pods** y esperar a que el web-spider cambie su estado a Succeed, lo que significará que ha terminado su ejecución.  

#### 8. Inicie el flujo del spark-job

Después de que la ejecución del web-spider ha terminado, puede empezar el flujo del spark-job de la misma forma.  
El spark job está definido como un CronJob en Kubernetes.  Para poder ejecutar su flujo sin esperar su horario programado debe dirigirse a **Workloads --> Cron Jobs** y seleccionar el spark-job y usar la opción "Trigger" para ejecutar el job de inmediato.  

> NOTA: 
> IMAGEN

Una vez realizado este paso, puede dirigirse a la sección de **Pods** y esperar a que el spark-job cambie su estado a Succeed, lo que significará que ha terminado su ejecución.  

#### 9. Acceda a Kibana para consultar los datos y transformaciones  
  
Una vez que el **spark-job** haya terminado su ejecución y el pod cambie su estado a **Succeed**, los datos ya estarán disponibles en **Elasticsearch** y podrán consultarse mediante **Kibana**.  
Para ingresar a Kibana:  
- Ingrese a **Network --> Services**. y seleccione el serivio llamado `ic4302-kb-http`
- Seleccione la opción **Port Forward** para exponer el servicio en su máquina local.  Inmediatamente se abrirá un enlace en su navegador para poder ingresar a la pagina de inicio.
- Ingrese los datos de inicio de sesión
 ```
User: `elastic`
Password:** debe obtenerse desde Lens:
 ```
- Para obetner la contraseña, debe ingresar a **Config --> Secrets**, seleccionar `ic4302-es-elastic-user` y copie el valor de la contraseña y peguelo en el inicio de sesión.

Una vez haya completado estos pasos, puede crear consultas para ver los documentos almacenados y verificar los nuevos campos.  
  

> NOTA: 
> IMAGEN


---
</details>

## 5. Pruebas

<details>
  <summary>Desplegar información</summary>

### 5.1 Pruebas Unitarias
- Extracción de count de API de Pubmed ![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/pruebas_pubmed_web-spider.png)
- Obtener lista de ids de API de Pubmed ![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/pruebas_pubmed_web-spider.png)
- Inicializar job con los campos correctos ![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/pruebas_pubmed_web-spider.png)
- Insertar job en MariaDB ![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/pruebas_MariaDB_web-spider.png)
- Enviar job_id por RabbitMQ ![Resultados](https://github.com/carayac/2025-02-IC4302/blob/proyecto-opcional/PO/images/pruebas_RabbitMQ_web-spider.png)

- Scripts en Python para validar la correcta conexión con PubMed y Crossref.  
- Funciones para verificar transformación de fechas y autores en Spark SQL.  



### 5.2 Pruebas Funcionales
- Verificar que los *jobs* se crean en MariaDB.  
- Verificar que los *jobs-id* se envían a través del canal de RabbitMQ.
- Comprobar que los documentos se guardan en JSON.  
- Confirmar que Elasticsearch contiene los documentos procesados.  
- Visualizar en Kibana los resultados.  

---

</details>

## 6. Resultados

<details>
  <summary>Desplegar información</summary>

- Número de artículos procesados.  
- Ejemplos de documentos transformados en Elasticsearch.  
- Evidencia de búsquedas realizadas en Kibana.  

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
*(al menos 10 conclusiones)*  

### 7.2 Recomendaciones
1. Siempre implementar prints mediante los procesos, de manera que se puede seguir todo paso a paso y ver los resultados que están dando las funciones para verificar si son correctos 
2. Todas las funciones manejarlas con try y errores, ya que es muy útil para reconocer el fallo en específico a la hora de hacer las pruebas, además facilita mucho el proceso de correcciones  
3. El uso de variables de entorno permiten separar la configuración del código, lo que facilita su mantenimiento, y aumenta la portabilidad entre distintos entornos y reduce la complejidad al realizar cambios o actualizaciones en este caso fue de utilidad para rutas y credenciales.
4. Se recomienda investigar previamente las tecnologías poco conocidas o con limitada comprensión, ya que esto facilita su aplicación en el desarrollo de proyectos, mejora la comprensión de su funcionamiento y agiliza la solución de errores.
5. Es recomendable probar los distintos componentes del software por separado antes de integrarlos, para poder detectar problemas específicos antes de que afecten todo el sistema. 
6. Hacer un control de versiones y documentar los cambios en el código, usando herramientas como GitHub, para facilitar la colaboración en equipo y la recuperación y restauración del código anterior en caso de  errores accidentales. 
   
*(al menos 10 recomendaciones)*  

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


---
</details>
