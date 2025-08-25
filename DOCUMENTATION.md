# Proyecto Opcional - Crossref Search

**Curso:** IC4302 - Bases de Datos II  
**Institución:** Tecnológico de Costa Rica  
**Escuela:** Ingeniería en Computación  
**Semestre:** Segundo Semestre 2025  

---
## 📖 Índice
🌎 [Introducción](#1-introducción)  
  
🌎 [Objetivos](#2-objetivos)  
  
🌎 [Arquitectura del Sistema](#3-arquitectura-del-sistema)  
  
🌎 [Instrucciones de ejecución](#4-instrucciones-de-ejecución)  
  
🌎 [Pruebas](#5-pruebas)  
  
🌎 [Resultados](#6-resultados)  
  
🌎 [Conclusiones y Recomendaciones](#7-conclusiones-y-recomendaciones)  
  


## 1. Introducción
Este documento describe el desarrollo e implementación del proyecto **Crossref Search**, cuyo propósito es construir un motor de búsqueda de artículos científicos utilizando las APIs de la **National Library of Medicine (PubMed)** y **Crossref**.  

---

## 2. Objetivos

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

## 3. Arquitectura del Sistema
El sistema está compuesto por los siguientes servicios:

- **Web Spider (Python, Kubernetes CronJob):** consulta periódicamente PubMed y organiza los artículos en *jobs*.  
- **Downloader (Python, Kubernetes Deployment):** recibe los *jobs*, descarga metadatos desde PubMed y Crossref, y guarda los resultados en JSON.  
- **Spark Job (Scala, Kubernetes CronJob):** procesa los datos, realiza transformaciones con Spark SQL y los indexa en Elasticsearch.  

Los servicios se comunican mediante **RabbitMQ**, y los datos son almacenados en **MariaDB** y **Elasticsearch**, permitiendo su consulta a través de **Kibana**.

---

## 4. Instrucciones de Ejecución

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

## 5. Pruebas

### 5.1 Pruebas Unitarias
- Scripts en Python para validar la correcta conexión con PubMed y Crossref.  
- Funciones para verificar transformación de fechas y autores en Spark SQL.  



### 5.2 Pruebas Funcionales
- Verificar que los *jobs* se crean en MariaDB.  
- Comprobar que los documentos se guardan en JSON.  
- Confirmar que Elasticsearch contiene los documentos procesados.  
- Visualizar en Kibana los resultados.  

---

## 6. Resultados
- Número de artículos procesados.  
- Ejemplos de documentos transformados en Elasticsearch.  
- Evidencia de búsquedas realizadas en Kibana.  

---

## 7. Conclusiones y Recomendaciones

### 7.1 Conclusiones
1. ...  
2. ...  
3. ...  
*(al menos 10 conclusiones)*  

### 7.2 Recomendaciones
1. ...  
2. ...  
3. ...  
*(al menos 10 recomendaciones)*  

---

## 8. Referencias
- [Apache Spark](https://spark.apache.org/)  
- [Crossref API](https://api.crossref.org)  
- [PubMed API](https://eutils.ncbi.nlm.nih.gov/)  
- [Kubernetes Documentation](https://kubernetes.io/)  
- [Docker Documentation](https://docs.docker.com/)  

---
