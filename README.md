# IC4302 - Tarea Corta: Observability

**Curso:** Bases de Datos II (IC4302)  
**Semestre:** Segundo Semestre 2025  
**Institución:** Tecnológico de Costa Rica – Escuela de Ingeniería en Computación  


# Instrucciones de Ejecución
  
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


#### 1. Descargue el repositorio de la tarea corta en su computadora 
  
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
En su proyecto, ingrese a la carpeta de charts **-->** app **-->** templates **-->** values.yaml y reemplace el la imagen por su usuario correspondiente en docker hub, además reemplace el nombre de la imagen que desee probar segun las imagenes especificadas en la seccion *Imagenes Disponibles*:  
  
 ```
config:
  image: usuario/imagen

config:
  usuario/dataseeder
 ```

#### 3.2 Configure la carga y uso de las bases de datos

En caso de desear la ejecucion de solamente una base en especifico, ingrese a charts **-->** databases **-->** values.yaml en la cual usted podra modificar los campos enbale true = ejecutar base de datos, false = no ejecutar la base de datos.
```yaml
  elastic:
    enabled: false #Coloque segun su prefertencia
    version: 8.6.1
    replicas: 1 #minimo 3 datanodes
    name: ic4302
```
##### Configuracion de la carga de datos

Con la finalidad de evitar el llenado de bases de datos que no estan en ejecucion se establece un mecanismo similar al anterior en el cual dentro de charts **-->** app **-->** `values.yaml` podra colocar en `true` las bbases que se desear cargar. 

> [!IMPORTANT]  
> La duracion de construccion de la imagen dataseeder puede tardar unos minutos.

```yaml
    dataseeder: # Added configuration for DataSeeder
        enabled: true
        name: dataseeder
        replicas: 1
        image: darcecampos/dataseeder # To charge with data the database
        postgresEnable: true
        mariaDBEnable: false
        elasticSearchEnable: false
        vespaEnable: false
        chromaDBEnable: false
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

</details>

# Configuracion de las herramientas

# Maria DB

<details>
  <summary>Desplegar información</summary> 

Para Maria DB se utiliza la versión Open Source de MySQL. Esta configuración cumple con los requisitos solicitandos con:  
- **Alta disponibilidad** mediante un clúster con un *primary* y dos *replicas*.  
- **Persistencia de datos** con volúmenes de almacenamiento tanto para el nodo primario como para las replicas, estos con 8Gi de tamaño para el volumen.
Al realizar estas modificaciones aseguramos **escalabilidad** al incrementar las replicas que de igual manera puede aumentarse segun la carga de lectura.  También se asegura la **alta disponibilidad** en caso de que el nodo primario falle, una réplica puede mantener el servicio.

 ```yaml
  primary:
    persistence:
      enabled: true
      size: 8Gi
  secondary: #Minimo 2 replicas
    persistence:
      replicas: 2 
      enabled: true
      size: 8Gi
``` 
- El **Monitoreo** se realiza mediante la exposición de métricas de Prometheus habilitando la exportación de métricas desde Maria DB y la integración con el operador en Prometheus.  
 ```yaml
  metrics:
    enabled: true
    serviceMonitor:
      enabled: true
 ```



</details> 

# PostgreSQL

<details>
  <summary>Desplegar información</summary> 

Para la configuración de esta base de datos se habilita almacenamiento persistente para el nodo primario y un tamaño de 8Gi para el volumen de este.  También se habilita una unica replica con el mismo tamaño que el nodo primario.  
Al realizar estas modificaciones aseguramos **escalabilidad** al incrementar las replicas que de igual manera puede aumentarse segun la carga de lectura.  También se asegura la **alta disponibilidad** en caso de que el nodo primario falle, una réplica puede mantener el servicio.  
 ```yaml
primary:
    persistence:
      enabled: true
      size: 8Gi           
  readReplicas:
    replicaCount: 1
    persistence:
      enabled: true
      size: 8Gi

 ```

- El **Monitoreo** se realiza mediante la exposición de métricas de Prometheus habilitando la exportación de métricas desde PostgreSQL y la integración con el operador en Prometheus.  
 ```yaml
  metrics:
    enabled: true
    serviceMonitor:
      enabled: true
 ```

</details> 


# Elasticsearch

<details>
  <summary>Desplegar información</summary> 

  AQUI INFO

</details> 


# Redis y Memcached

<details>
  <summary>Desplegar información</summary> 

### Memcached
Para la realización de esta tarea se implementa Memcached, un sistema de caché en memoria distribuido, utilizado principalmente para acelerar el sistema al reducir la carga de la base de datos. Este también s eutiliza para exponer métricas de Memcached en formato Prometheus.
 ```yaml
  metrics:
    enabled: true
    serviceMonitor:
      enabled: true
 ```

Para la implementación de caché en todos los mos motores de bases de datos, se intenta recuperar el valor a partir de una clave, si este existe entonces sería un caché hit para que sea devuelto a la solicitud,  En caso de no encontrarse, se registra un caché miss y se procede a realizar la consulta directamente a la base de datos y posteriormente alamcena el resultado en Memcached.
</details> 


# Prometheus y Grafana

<details>
  <summary>Desplegar información</summary> 

  Con la finalidad de obtener las métricas específicas de las bases de datos, diferenciando entre el uso de cachés, ya sea memcached o redis, se crearon métricas personalizadas con labels que permite recolectar la información marcando estas diferencias. 
  ```
  peticiones_http = Counter('total_peticiones_http', 'Total peticiones HTTP', ['bd', 'cache'])
  promedio_tiempo = Histogram('promedio_tiempo_consulta', 'Tiempo promedio de consultas', ['bd', 'cache'])
  ```
  Estas métricas las scrapea el operador de prometheus por medio de un service y un service monitor, donde será guardado en el scraping de prometheus.
  Si queremos ver si se encuentra el endpoint en la interfaz de prometheus, podemos hacer port-forward al poner los siguientes comandos en bash:
  ```
    kubectl port-forward -n monitoring prometheus-monitoring-stack-prometheu-prometheus-0 9090:9090
  ```
  Y luego podemos acceder a la interfaz en la siguiente dirección en nuestro navegador:
  ```
    http://localhost:9090
  ```
  Una vez dentro de la interfaz de prometheus, ingresamos a -> status -> targets, y buscamos el target que diga "flasktest". Si el scraping se hizo correctamente, aparecerá en estado "up".


  Para ver los dashboards en grafana, primero debemos habilitar los dashboards que queremos ver en el proyecto en grafana.config -> values.yalm
  ```yalm
  dashboards:
    elasticsearch:
      name: elasticsearch
      file: elasticsearch.json
      enable: true
  ```
  Grafana está configurado para obtener como data source a prometheus. Para poder ver la interfaz de grafana, podemos hacer port-forward:
  ```
    kubectl port-forward pod/grafana-deployment-787b9688d8-dz29k 3000:3000 -n monitoring
  ```
  Y podemos acceder con las credenciales en:
  ```
    http://localhost:3000
  ```
  Credenciales: user -> admin, pass -> LTRnsh1AAWNZGA==

  Una vez que ingresamos, buscamos la sección de dashboards. En la sección de dashboards ingresamos a "Monitoring", y ahí encontraremos el dashboard de la base de datos que queremos ver.

</details> 


# API Flask

<details>
  <summary>Desplegar información</summary>  


El presente componente representa los endpoints que permiten hacer pruebas de consultas a las diferentes bases de datos a las cuales se les aplica obsevabilidad.
## Documentación de Imágenes y Configuración en `values.yaml`

Este proyecto soporta diferentes imágenes de base de datos y variantes con Memcached o Redis como mecanismos de cache.  
El cambio de imagen se realiza modificando el archivo `values.yaml` en la sección correspondiente al despliegue de la API.

---

### Imágenes Disponibles

| Servicio       | Imagen Base         | Memcached           | Redis             |
|----------------|------------------|-------------------|-----------------|
| **ChromaDB**    | usuario/chroma     | usuario/chroma-memcached | usuario/chroma-redis |
| **Elasticsearch** | usuario/elasticsearch | usuario/elasticsearch-memcached | usuario/elasticsearch-redis |
| **MariaDB**     | usuario/mariadb    | usuario/mariadb-memcached | usuario/mariadb-redis |
| **PostgreSQL**  | usuario/postgresql | usuario/postgresql-memcached | usuario/postgresql-redis |
| **Vespa.ai**  | usuario/vespa | usuario/vespa-memcached | usuario/vespa-redis |


> **Nota:** Reemplace `usuario` por tu nombre de usuario en DockerHub (ejemplo: `mydockeruser/mariadb`).

---

## Configuración en `values.yaml`

En el archivo `values.yaml`, se define la imagen que utilizará el despliegue.  
La sección típica es la siguiente:

```yaml
config:
  flask:
    enabled: true
    name: flasktest
    replicas: 10
    image: usuario/imagen
```

### Ejemplo: Usar ChromaDB con Memcached
```yaml
config:
  flask:
    enabled: true
    name: flasktest
    replicas: 10
    image: usuario/chroma-memcached
```
---

# Dataset de Prueba: Información de Animales

Este apartado describe el dataset utilizado como prueba en el proyecto.  
El dataset proporciona información general sobre diversas especies animales, abarcando datos físicos, ecológicos, taxonómicos y de comportamiento.  

Fuente original: [Animal Information Dataset - Kaggle](https://www.kaggle.com/datasets/iamsouravbanerjee/animal-information-dataset)

---

## Descripción General

El dataset reúne un conjunto de características asociadas a distintos animales, como su altura, peso, dieta, hábitat, depredadores, estado de conservación, entre otros.  
Este recurso fue empleado como dataset de prueba para validar funcionalidades en el proyecto, ya que contiene datos variados que permiten realizar consultas, análisis y visualizaciones desde distintos enfoques.

---

## Estructura del Dataset

El dataset está compuesto por diversas columnas (atributos) que describen a cada animal. A continuación se detalla el glosario columna por columna:

| Columna                  | Descripción                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| **Animal**               | Nombre del animal.                                                          |
| **Height (cm)**          | Rango de altura en centímetros del animal.                                  |
| **Weight (kg)**          | Rango de peso en kilogramos del animal.                                     |
| **Color**                | Colores comunes asociados a la apariencia del animal.                       |
| **Lifespan (years)**     | Promedio de años de vida del animal.                                        |
| **Diet**                 | Tipo de dieta que sigue principalmente (Ejemplo: carnívoro, herbívoro).     |
| **Habitat**              | Hábitat o entorno natural donde suele encontrarse el animal.                 |
| **Predators**            | Depredadores o enemigos naturales del animal.                               |
| **Average Speed (km/h)** | Velocidad promedio en kilómetros por hora.                                  |
| **Countries Found**      | Países o regiones donde el animal es comúnmente encontrado.                 |
| **Conservation Status**  | Estado de conservación según organismos especializados (Ejemplo: En peligro).|
| **Family**               | Familia taxonómica a la que pertenece el animal.                            |
| **Gestation Period (days)** | Rango en días del período de gestación o embarazo.                      |
| **Top Speed (km/h)**     | Velocidad máxima alcanzable en kilómetros por hora.                         |
| **Social Structure**     | Estructura social o comportamiento (Ejemplo: solitario, en grupo).          |
| **Offspring per Birth**  | Número típico de crías por evento reproductivo.                             |

---
 
# Esquema Relacional del Dataset de Animales - MariaDB

Este apartado describe la estructura de base de datos SQL diseñada para almacenar el dataset de prueba sobre animales.  
La implementación sigue un modelo relacional normalizado, con separación de entidades principales y relaciones uno a muchos y muchos a muchos.

---

![alt text](DiagramaSQL.jpg)

---

### Mapeo de las bases documentales 
 ```json
{
  "animals": {
    "mappings": {
      "properties": {
        "average_speed_kmh": {
          "type": "keyword"
        },
        "color": {
          "type": "keyword"
        },
        "conservation_status": {
          "type": "keyword"
        },
        "countries_found": {
          "type": "text"
        },
        "diet": {
          "type": "keyword"
        },
        "family": {
          "type": "keyword"
        },
        "gestation_period_days": {
          "type": "keyword"
        },
        "habitat": {
          "type": "text"
        },
        "height_cm": {
          "type": "keyword"
        },
        "lifespan_years": {
          "type": "keyword"
        },
        "name": {
          "type": "keyword"
        },
        "offspring_per_birth": {
          "type": "keyword"
        },
        "predators": {
          "type": "text"
        },
        "social_structure": {
          "type": "text"
        },
        "top_speed_kmh": {
          "type": "keyword"
        },
        "weight_kg": {
          "type": "keyword"
        }
      }
    }
  }
 ```

# Endpoints de prueba 
Base URL: http://localhost:30080/

Esta API permite consultar información sobre animales y sus características.

---

## Endpoints

### 1. Health Check

**GET** /health

Verifica que el servicio está activo y funcionando.

**Request:**
GET http://localhost:30080/health

**Response:**
{
  "status": "healthy"
}

Código de estado: 200 OK

---

### 2. Listar Animales

**GET** /animales

Devuelve los primeros 50 animales registrados en la base de datos.

**Request:**
GET http://localhost:30080/animales

**Response exitoso (200 OK):**
[
  {"id": 1, "nombre": "Tigre"},
  {"id": 2, "nombre": "León"},
  ...
]

**Response de error (500 Internal Server Error):**
{
  "error": "No se pudo conectar a la base de datos"
}

Notas:
- Utiliza un pool de conexiones a PostgreSQL.
- Se asegura de cerrar el cursor y devolver la conexión al pool.

---

### 3. Animales listados por su color

**GET** /colores

Devuelve los animales organizados por sus colores.

**Request:**
GET http://localhost:30080/colores

**Response exitoso (200 OK):**
[
   {
        "animals": "Uakari",
        "color": "Bald, Red"
   }
]

**Response de error (500 Internal Server Error):**
{
  "error": "No se pudo conectar a la base de datos"
}

---

## Resumen de Endpoints

| Endpoint         | Método | Descripción                                | Response Ejemplo                      | Código Estado |
|-----------------|--------|--------------------------------------------|--------------------------------------|---------------|
| /health         | GET    | Verifica que el servicio está activo       | {"status": "healthy"}              | 200           |
| /animales       | GET    | Lista los primeros 50 animales             | [{"id":1,"nombre":"Tigre"},...]  | 200 / 500     |
| /colores        | GET    | Lista los colores y los animales           | [{"animals":"Guepardo","color":"grey"},...] | 200 / 500 |

## Llenado de las bases de datos a utilizar
Con la finalidad de generar el llenado de las bases de datos, el software ofrece un componente de tipo job, el cual representa el dataseeder, basado en la imagen que llenas las bases de datos. Este proceso se ejecuta al instante de realizar la instalacion.



</details>


---
# Pruebas de cargas

<details>
  <summary>Desplegar información</summary> 

Se implementan pruebas de carga mediante la herramienta de código abierto Gatling. La misma se se integra en la tarea mediante plugins compilados por Maven, definidos en el archivo "pom.xml". 

Pasos para correr las pruebas de carga:

1. Si no tiene en su equipo Maven, instalarlo y añadirlo a variables de entorno, se puede seguir el siguiente ejemplo: https://www.youtube.com/watch?v=rl5-yyrmp-0
   
2. Gatling corre el archivo src/test/java/simulations/GatlingTest.Java; al principio del archivo se pueden encontrar las siguientes variables:
   
   int users = 100;
   
   int time = 900;

   Estas se pueden modificar con la cantidad de usuarios con los que se desea hacer la carga y la duración de la prueba en segundos que se desea.
   
4. En la terminal bash acceder a la carpeta TC1 dentro del repositorio:
      ```
      cd 2025-02-IC4302/TC1
      ```
5. Correr el comando "mvn gatling:test", esto ejecuta las pruebas y da actualizaciones en vivo en la terminal.
6. Al finalizar la prueba, se guarda el resultado en target/gatling/<nombre de la prueba y fecha/index.html
   Se puede abrir en internet y ver los datos de la prueba de carga. 

---

## Pruebas de cargar realizadas
En el presente apartado se desarrollan los tests realizados por cada motor de bases de datos.

### Configuracion del entorno de pruebas
#### Motores de bases de datos evaluados
- MariaDB
- PostgreSQL
- Elasticsearch
- ChromaDB
- Vespa.ia

#### Configuraciones de Cache por motor
- Sin caché
- Con Redis
- Con Memcached

#### Endpoints Evaluados
- GET /animales
- GET /colores

### Pruebas por Motor de Base de Datos

<details>
  <summary>Maria DB</summary> 

#### MariaDB
##### Prueba 1: MariaDB Sin Caché - Endpoint /animales

###### Configuración

###### Resultados

##### Prueba 2: MariaDB Con Redis - Endpoint /animales

###### Configuración

###### Resultados

##### Prueba 3: MariaDB Con Memcached - Endpoint /animales

###### Configuración

###### Resultados

##### Prueba 4: MariaDB Con Redis - Endpoint /colores

###### Configuración

###### Resultados

##### Prueba 5: MariaDB Con Memcached - Endpoint /colores

###### Configuración

###### Resultados

</details> 

<details>
  <summary>Elasticsearch</summary> 

#### Elasticsearch
##### Prueba 1: Elasticsearch Sin Caché - Endpoint /animales

###### Configuración

  Configuración de Caché: Sin caché

  Endpoint Probado: /animales

  Usuarios Concurrentes: 100

  Duración: 900 segundos (15 minutos)

  Patrón de Carga: Ramp-up gradual de usuarios

###### Resultados
```cmd
                              505 (OK=505    KO=0     )
> min response time                                      8 (OK=8      KO=-     )
> max response time                                    527 (OK=527    KO=-     )
> mean response time                                    16 (OK=16     KO=-     )
> std deviation                                         25 (OK=25     KO=-     )
> response time 50th percentile                         13 (OK=13     KO=-     )
> response time 75th percentile                         15 (OK=15     KO=-     )
> response time 95th percentile                         24 (OK=24     KO=-     )
> response time 99th percentile                         33 (OK=33     KO=-     )
> mean requests/sec                                  0.562 (OK=0.562  KO=-     )
---- Response Time Distribution ------------------------------------------------
> t < 800 ms                                           505 (100%)
> 800 ms <= t < 1200 ms                                  0 (  0%)
> t >= 1200 ms                                           0 (  0%)
> failed                                                 0 (  0%)
================================================================================
```

FOTO GRAFANAAA

###### Conclusiones

##### Prueba 2: Elasticsearch Con Redis - Endpoint /animales

###### Configuración
  Configuración de Caché: Con caché Redis

  Endpoint Probado: /animales

  Usuarios Concurrentes: 100

  Duración: 900 segundos (15 minutos)

  Patrón de Carga: Ramp-up gradual de usuarios

###### Resultados

##### Prueba 3: Elasticsearch Con Memcached - Endpoint /animales

###### Configuración
  Configuración de Caché: Con caché Memcached

  Endpoint Probado: /animales

  Usuarios Concurrentes: 100

  Duración: 900 segundos (15 minutos)

  Patrón de Carga: Ramp-up gradual de usuarios

###### Resultados

##### Prueba 4: Elasticsearch Con Redis - Endpoint /colores

###### Configuración
  Configuración de Caché: Con caché Redis

  Endpoint Probado: /colores

  Usuarios Concurrentes: 100

  Duración: 900 segundos (15 minutos)

  Patrón de Carga: Ramp-up gradual de usuarios

###### Resultados

##### Prueba 5: Elasticsearch Con Memcached - Endpoint /colores

###### Configuración
  Configuración de Caché: Con caché Memcached

  Endpoint Probado: /colores

  Usuarios Concurrentes: 100

  Duración: 900 segundos (15 minutos)

  Patrón de Carga: Ramp-up gradual de usuarios
###### Resultados

</details> 

<details>
  <summary>PostgreSQL</summary> 

#### MariaDB
##### Prueba 1: PostgreSQL Sin Caché - Endpoint /animales

###### Configuración

###### Resultados

##### Prueba 2: PostgreSQL Con Redis - Endpoint /animales

###### Configuración

###### Resultados

##### Prueba 3: PostgreSQL Con Memcached - Endpoint /animales

###### Configuración

###### Resultados

##### Prueba 4: PostgreSQL Con Redis - Endpoint /colores

###### Configuración

###### Resultados

##### Prueba 5: PostgreSQL Con Memcached - Endpoint /colores

###### Configuración

###### Resultados

</details> 

<details>
  <summary>ChromaDB</summary> 

#### MariaDB
##### Prueba 1: ChromaDB Sin Caché - Endpoint /animales

###### Configuración

###### Resultados

##### Prueba 2: ChromaDB Con Redis - Endpoint /animales

###### Configuración

###### Resultados

##### Prueba 3: ChromaDB Con Memcached - Endpoint /animales

###### Configuración

###### Resultados

##### Prueba 4: ChromaDB Con Redis - Endpoint /colores

###### Configuración

###### Resultados

##### Prueba 5: ChromaDB Con Memcached - Endpoint /colores

###### Configuración

###### Resultados

</details> 

<details>
  <summary>Vespa.ai</summary> 

#### MariaDB
##### Prueba 1: Vespa.ai Sin Caché - Endpoint /animales

###### Configuración

###### Resultados

##### Prueba 2: Vespa.ai Con Redis - Endpoint /animales

###### Configuración

###### Resultados

##### Prueba 3: Vespa.ai Con Memcached - Endpoint /animales

###### Configuración

###### Resultados

##### Prueba 4: Vespa.ai Con Redis - Endpoint /colores

###### Configuración

###### Resultados

##### Prueba 5: Vespa.ai Con Memcached - Endpoint /colores

###### Configuración

###### Resultados

</details> 

</details> 


# Recomendaciones
1. Mantener consistencia en los nombres de las imagenes a utilizar: `servicio-cache` (`-memcached`, `-redis`).
2. Utiliza variables de entorno que permitan las parametrizacion de los datos necesarios para las bases de datos.
3. Dedicar tiempo a entender la funcionalidad de implementar algunas bases de datos con varias replicas y sus nodos master, y comoe estos reaccionan ante fallos y disponibilidad de datos.
4. Establecer un buen lapso de TTL (tiempo de expiracion en caché) que esté adaptado a su modelo y así garantizar consistencia en lo que se almacena en Memcached y lo que está en la base de datos.
5. Unificar el formato de salida en los endpoints, a pesar de que cada base de datos maneje estructuras distintas, es importante que los endpoints devuelvan respuestas consistentes (por ejemplo, JSON con los mismos campos y nombres). Esto facilita la comparación de resultados y el análisis en pruebas de carga.
6. Incluir flags que permitan habilitar o deshabilitar las variables de entorno de cada DB, de esta manera se puede ir probando el dataseeder completo sin tener que eliminar funciones y variables de otras bases que no están activas.
7. Es importante seleccionar métricas relevantes para scrapear y mostrar en grafana, ya que esta es la manera más optimizada de recolectar información para una mejor observabilidad sin crear ruido de métricas innecesarias.
8. Se debe mantener la consistencia en la configuración de los service y service monitors para evitar problemas y fallos a la hora de scrapear las métricas con prometheus. 

# Conclusiones

1. Este dataset sirvió como recurso de prueba para el proyecto debido a su diversidad de atributos, lo cual permitió validar distintos procesos de manejo y análisis de información.  
2. Gracias a la variedad de datos incluidos, fue posible simular escenarios realistas y robustos dentro del entorno de desarrollo.
3. Implementar Memcached es realmente sencillo de implementar y permite que el tiempo de respuesta sea bastante reducido gracias al almacenamiento en memoria.
4. La implementación de nuevas bases de datos permitió conocer diferentes maneras de poder acceder a ellas y de configurarlas implementando los requisitos que cada una de ellas solicitaban.  Todo estó permitió el fortalecimeinto de habilidades dentro de las personas del equipo con herramientas antes desconocidas.
5. El uso de endpoints unificados permitió abstraer las diferencias entre motores SQL y NoSQL, logrando que la API presentara los mismos resultados.
6. La configuración del dataseeder y bases de datos, con la posibilidad de activar o desactivarlas con sus respectivas variables de entorno, demostró ser útil para optimizar las pruebas y garantizar un desarrollo más controlado.
7. Las métricas personalizadas dieron una visión clara de cómo los usuarios interactúan con la aplicación y qué tan eficiente es el uso de caché en cada base de datos.
8. Grafana es un muy buen complemento de prometheus, ya que convierte métricas en paneles intuitivos e interactivos, que facilitan la comprensión de las métricas.


# Referencias
https://pymemcache.readthedocs.io/en/latest/getting_started.html  
https://github.com/vespa-engine/sample-apps/tree/master/examples/agentic-streamlit-chatbot/advanced_app/app  
https://docs.trychroma.com/
https://www.elastic.co/docs/reference/elasticsearch/clients/python
https://www.postgresql.org/docs/current/
https://flask.palletsprojects.com/en/stable/
https://www.sbert.net/index.html
https://helm.sh/docs/
https://docs.docker.com/reference/cli/docker/image/
https://requests.readthedocs.io/en/latest/
https://docs.trychroma.com/docs/overview/introduction
https://prometheus.io/docs/concepts/metric_types/
https://prometheus.github.io/client_python/instrumenting/labels/
https://prometheus.github.io/client_python/instrumenting/counter/
https://prometheus.github.io/client_python/instrumenting/histogram/
https://dkbalachandar.wordpress.com/2025/07/21/kubernetes-servicemonitor-explained-how-to-monitor-services-with-prometheus/
https://flask.palletsprojects.com/en/stable/api/#flask.Flask.before_request
https://flask.palletsprojects.com/en/stable/api/#flask.Flask.after_request
https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/developer/getting-started.md#using-servicemonitors


