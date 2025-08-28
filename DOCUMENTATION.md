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
  
Este documento describe el desarrollo e implementación del proyecto **Crossref Search**, cuyo propósito es construir un motor de búsqueda de artículos científicos utilizando las APIs de la **National Library of Medicine (PubMed)** y **Crossref**.  
  
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
1. Clonar el repositorio:  
   ```bash
   git clone <URL_REPO>
   cd crossref-search
   ```

   ```

---
</details>

## 5. Pruebas

<details>
  <summary>Desplegar información</summary>

### 5.1 Pruebas Unitarias
- Extracción de count de API de Pubmed
- Obtener lista de ids de API de Pubmed
- Inicializar job con los campos correctos

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

---
</details>
