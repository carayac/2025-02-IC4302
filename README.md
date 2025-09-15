# IC4302 - Tarea Corta: Observability

**Curso:** Bases de Datos II (IC4302)  
**Semestre:** Segundo Semestre 2025  
**Institución:** Tecnológico de Costa Rica – Escuela de Ingeniería en Computación  

# Configuracion de las herramientas

# Maria DB
# PostgreSQL
# Elasticsearch
# Redis y Memcached
# Prometheus y Grafana

# API Flask
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

  PONER DIAGRAMA MARIA



---



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

#### Definicion de bases de datos a cargar
Con la finalidad de evitar el llenado de bases de datos que no estan en ejecucion se establece un mecanismo en el cual dentro de `values.yaml` podra colocar en `true` las bbases que se desear cargar. 

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

---
# Pruebas de cargas


# Recomendaciones
1. Mantener consistencia en los nombres de las imagenes a utilizar: `servicio-cache` (`-memcached`, `-redis`).
2. Utiliza variables de entorno que permitan las parametrizacion de los datos necesarios para las bases de datos.
3. Dedicar tiempo a entender la funcionalidad de implementar algunas bases de datos con varias replicas y sus nodos master, y comoe estos reaccionan ante fallos y disponibilidad de datos.
4. Establecer un buen lapso de TTL (tiempo de expiracion en caché) que esté adaptado a su modelo y así garantizar consistencia en lo que se almacena en Memcached y lo que está en la base de datos.

# Conclusiones

1. Este dataset sirvió como recurso de prueba para el proyecto debido a su diversidad de atributos, lo cual permitió validar distintos procesos de manejo y análisis de información.  
2. Gracias a la variedad de datos incluidos, fue posible simular escenarios realistas y robustos dentro del entorno de desarrollo.
3. Implementar Memcached es realmente sencillo de implementar y permite que el tiempo de respuesta sea bastante reducido gracias al almacenamiento en memoria.
4. La implementación de nuevas bases de datos permitió conocer diferentes maneras de poder acceder a ellas y de configurarlas implementando los requisitos que cada una de ellas solicitaban.  Todo estó permitió el fortalecimeinto de habilidades dentro de las personas del equipo con herramientas antes desconocidas.


# Referencias
https://pymemcache.readthedocs.io/en/latest/getting_started.html  
https://github.com/vespa-engine/sample-apps/tree/master/examples/agentic-streamlit-chatbot/advanced_app/app  

