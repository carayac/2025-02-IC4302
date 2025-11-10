# IC4302 - Proyecto 02: Products Search V2

**Curso:** Bases de Datos II (IC4302)  
**Semestre:** Segundo Semestre 2025  
**Institución:** Tecnológico de Costa Rica – Escuela de Ingeniería en Computación  

### VIDEO INFORMATIVO
[Que es NOMBRE DE LA UI?](poner link)

# Instrucciones de Ejecución
  
<details>
  <summary>Desplegar información</summary> 

### 1.1 Requisitos Previos
- Cuenta en Docker Hub: Es un sitio web donde puedes guardar y compartir imágenes de programas listos para usar. Es como una "nube" para aplicaciones.
- Docker y Docker Compose: Docker es una herramienta que permite ejecutar programas en "contenedores", que son como cajas que traen todo lo necesario para que el programa funcione igual en cualquier computadora. Docker Compose ayuda a iniciar varios de estos programas juntos fácilmente.
- Kubernetes (Minikube o Docker Desktop): Kubernetes es una plataforma que ayuda a administrar y ejecutar muchos contenedores a la vez, ideal para proyectos grandes. Minikube y Docker Desktop son formas sencillas de usar Kubernetes en tu propia computadora.
- Helm Charts instalados: Helm es una herramienta que facilita la instalación y actualización de aplicaciones en Kubernetes, usando "charts" que son como recetas pre-hechas.
- Git: Es una herramienta para guardar y controlar los cambios en el código de un proyecto, permitiendo trabajar en equipo y mantener un historial de versiones.
- Lens: Es un programa con interfaz gráfica que permite ver y administrar fácilmente los recursos y servicios que se están ejecutando en Kubernetes.
  
### 1.2 Instalación de Componentes  


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
> Sustituya la palabra usuario con su usario de Docker Hub

#### 3. Configure el registro de  las imágenes para el chart
En su proyecto, ingrese a la carpeta de charts **-->** app **-->** templates **-->** values.yaml y registre el nombre de usuario en docker hub que desea utilizar en el campo **docker_registry**  
  
 ```yaml
config:
  docker_registry: SU_USUARIO # docker registry replace with your own username
  producer:
    enabled: true
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


#### 6. Como ingresar a la pagina WEB 
<details>
  <summary>Desplegar información</summary>

### Manual de acceso a la página web 



</details>


</details>


# Pruebas Unitarias
  
<details>
  <summary>Desplegar información</summary> 

### Controller  
<details>
  <summary>Desplegar información</summary>



</details>

#### Web Scraper
<details>
  <summary>Desplegar información</summary>


</details>


### Beautiful Soup
<details>
  <summary>Desplegar información</summary>
  
</details>

#### Spacy Entity Extractor
<details> <summary>Desplegar información</summary>


</details>

### Spark Processor Job 
<details> <summary>Desplegar información</summary>

Para validar las transformaciones de Spark sin tocar la escritura en Mongo Atlas se añadió un conjunto de pruebas unitarias en `Services/docker/SparkProcessorJob/app/test.py`. Ejecutan un SparkSession local y cubren:

- `test_uppercase_first_letter_capitalizes_string_columns`: verifica que las columnas texto de primer nivel se conviertan a *Title Case* sin alterar tipos numéricos ni `None`.
- `test_normalize_entities_handles_nested_structures`: comprueba la capitalización dentro de arreglos y estructuras anidadas (`entities`, `comentarios`, `tags`).
- `test_format_dates_ddmmyyyy_sql_formats_dates`: asegura que `date_extracted` acepte variantes (`YYYY/MM/DD`, `YYYY-MM-DD`) y se normalice a `DD/MM/YYYY` preservando nulos.
- `test_summary_generates_short_description`: valida la creación de `short-description`, truncando textos largos con sufijo `...` y manteniendo cadenas vacías para valores nulos.
- `test_add_related_products_builds_related_list`: garantiza que las entidades comunes generen recomendaciones sin duplicados ni auto-referencias.


#### Resultado más reciente

```
 => [8/8] RUN pytest -s -vv test.py && sleep 20                                                                                       21.2s 
 => => # PASSED                                                                                                                            
 => => # test.py::test_normalize_entities_handles_nested_structures PASSED                                                                  
 => => # test.py::test_format_dates_ddmmyyyy_sql_formats_dates PASSED                                                                       
 => => # test.py::test_summary_generates_short_description PASSED                                                                           
 => => # test.py::test_add_related_products_builds_related_list PASSED                                                                      
 => => # ============================== 5 passed in 18.76s ==============================
```

</details>

</details>


# Configuración de componenetes 
<details>
  
  <summary>Desplegar información</summary>  

### Controller  
<details>
  <summary>Desplegar información</summary>  

El Controller es el primer componente del pipeline y actúa como coordinador general del sistema. Su función principal es revisar periódicamente los archivos HTML almacenados en AWS S3 y decidir cuáles deben ser procesados.  
Sus funciones principales son:  

-	Busca archivos HTML en carpetas específicas del bucket de AWS S3
-	Compara los archivos usando hash MD5 para saber si son nuevos o han sido modificados
-	Guarda información de cada archivo como el nombre, tamaño, estado en la base de datos, especificamente en la colección ingestion dentro de Mongo
-	Envía mensajes a RabbitMQ solo para archivos nuevos o modificados, iniciando el procesamiento para que el siguiente componente pueda utilizarlo.

Este componente se ejecuta como un CronJob de Kubernetes, esto quiere decir que tiene ejecución automática dependiendo de la configuración establecida, en este caso se ejecuta cada hora, pero puede ser adaptado según la necesidad.  

```
controller:
    enabled: true
    replicas: 1
    name: controller
    image: controller
    schedule: "0 * * * *"  #every hour
```


</details>

#### Web Scraper
<details>
  <summary>Desplegar información</summary>

  El web scraper es un pequeño código en python que se corre localmente fuera de kubernetes. Se encarga de recorrer la página de cursos online "edutin". Recorre las categorías "programacion", "cocina", "creativo", "salud", "negocio", "deporte", "psicologia", "ciencia", "cloud computing", "mantenimiento", "moda", "arte", "idiomas" y "marketing". Para esto, se usa selenium para hacer scroll en la página principal de edutin, y una vez que se hayan cargado suficientes cursos, se recupera el html de la página. Luego, se recorre el html en busca de la dirección que lleva a la información espcífica de cada curso. Cuando se encuentra, se extrae el html de esa dirección. Los html se descargan localmente en la carpeta "productos", y van numerados del 001 al 505. Una vez se han descargado los 505 cursos, estos se suben a la carpeta del bucket de aws, ic-tec-dataset/CARPETA_HCDCP/. Desde ahí se podrán recuperar los datos posteriormente.


</details>


### Beautiful Soup
<details>
  <summary>Desplegar información</summary>
  
</details>

#### Spacy Entity Extractor
<details> 
  <summary>Desplegar información</summary>  

El Spacy Entity Extractor es el tercer componente del pipeline y se encarga de analizar los textos procesados por BeautifulSoup para identificar y extraer entidades importantes como nombres de productos, organizaciones, fechas, y otros datos relevantes.  

Este componente trabaja de forma continúa escuchando mensajes enviados por RabbitMQ y realiza las siguientes tareas:  

-	Escucha mensaje sde RabbitMQ que indican que el archivo está listo para procesar.
-	Obtiene los archivos JSON de la carpeta raw que se encuentra en el disco compartido del proyecto y que fue creada por el componente de BeautifulSoup.
-	Usa el modelo de Spacy y su función NER (Named Entity Recognition) para identificar entidades en diferentes campos establecidos en los documentos obtenidos como.
-	Después de crear las entidades, crea nuevos archivos JSON y los almacena en la carpeta augmented para que sean procesados posteriormente por el componente de Spark
-	Por último, actualiza la base de datos estableciendo que el procesamiento de entidades ha finalizado y llevar un control de trazabilidad sobre los documentos.

Este componente se ejecuta como un deployment en kubernetes con un mínimo de dos replicas para aumentar la velocidad de procesamiento, a diferencia del controller, este componente está siempre activo y esperando por nuevos mensajes.

```
controller:
    enabled: true
    replicas: 1
    name: controller
    image: controller
    schedule: "0 * * * *"  #every hour
```


Para la implementación del modelo de Spacy se elige el modelo *es_core_news_lg* el cual está diseñado para manejar el idioma español y se utiliza su versión large, la cual tiene mucho mayor alcance a la hora de hacer la extracción de entidades.  Algunas de las entidades que reconoce son PER (personas), ORG (organizaciones), LOC (lugares), DATE (fechas), MONEY (cantidades monetarias)


</details>

### Spark Processor Job 
<details> <summary>Desplegar información</summary>

Este proceso automático toma la información enriquecida de los cursos y la deja ordenada para que pueda buscarse fácilmente. No se requiere intervención humana: el componente se ejecuta de forma periódica, limpia los datos y los publica, de modo que otros sistemas solo consumen información coherente y homogénea.

El Spark Processor Job se despliega como un CronJob de Kubernetes y ejecuta el pipeline definido en `Services/docker/SparkProcessorJob/app/functions.py`. Utiliza como parámetros las variables de entorno `URI_MONGODB` (destino en Atlas) y `VOLUMEN_PVC` (ruta del volumen compartido) y registra cada etapa con `logging` para que el monitoreo se realice desde los logs del contenedor. Su ejecución completa aborda los siguientes pasos operativos:

- **Ingesta controlada:** `createSession` inicializa Spark con la conexión a MongoDB y `read_augmented_data` carga la carpeta `augmented`, creando la vista `augmented_data` para habilitar consultas SQL durante la sesión.
- **Estandarización de textos:** `uppercase_first_letter` recorre todas las columnas de tipo string y `normalize_entities` se encarga de arreglos y estructuras anidadas, asegurando que cada texto comience con mayúscula sin perder información contextual.
- **Normalización temporal:** `format_dates_ddmmyyyy_sql` transforma `date_extracted` al formato `DD/MM/YYYY`, unificando criterios de reporting y control de versiones de los documentos procesados.
- **Resumen ejecutivo:** se expone el UDF `resumen_simple` mediante `summary`, que genera la columna `short-description` con un máximo de 140 caracteres conservando palabras completas, lo cual mejora el consumo en interfaces de búsqueda.
- **Contexto relacional:** `add_related_products` identifica coincidencias de entidades entre productos, elimina auto-referencias y deduplica resultados, dejando en `productos_relacionados` hasta 10 recomendaciones directamente utilizables por la UI.
- **Publicación confiable:** `save_to_mongodb` persiste el resultado final en la colección `documents` de MongoDB Atlas con modo `overwrite`, garantizando que la versión más reciente del dataset esté disponible para Atlas Search.

De esta manera, cada ejecución del CronJob entrega datos limpios, resumidos y enriquecidos con relaciones, listos para ser indexados y consumidos por el resto de la plataforma.

</details>

### Configuración Firestore
<details> <summary>Desplegar información</summary>


</details>

### Configuración Mongo Atlas
<details>
  <summary>Desplegar información</summary>

#### Índice Atlas Search `default`
- **Colección:** `ecomm.documents`
- **Objetivo:** habilitar búsqueda full-text con facets y highlighting sobre los productos normalizados por Spark.
- Nota: Se asignaron de tipo facet las caracterist6icas mas relevantes que seran utilizadas.
- **Mapping utilizado:**
  ```json
    {
    "mappings": {
      "dynamic": true,
      "fields": {
        "authorComment": {
          "type": "string"
        },
        "currency": [
          {
            "analyzer": "lucene.keyword",
            "searchAnalyzer": "lucene.keyword",
            "type": "string"
          },
          {
            "type": "stringFacet"
          }
        ],
        "date_extracted": {
          "type": "date"
        },
        "description": {
          "type": "string"
        },
        "entities": {
          "fields": {
            "type": {
              "analyzer": "lucene.keyword",
              "searchAnalyzer": "lucene.keyword",
              "type": "string"
            },
            "value": [
              {
                "type": "string"
              },
              {
                "type": "stringFacet"
              }
            ]
          },
          "type": "document"
        },
        "general_category": [
          {
            "type": "string"
          },
          {
            "analyzer": "lucene.keyword",
            "type": "autocomplete"
          },
          {
            "type": "stringFacet"
          }
        ],
        "language": [
          {
            "type": "string"
          },
          {
            "type": "stringFacet"
          }
        ],
        "price": [
          {
            "type": "number"
          },
          {
            "type": "numberFacet"
          }
        ],
        "productos_relacionados": {
          "fields": {
            "entities": {
              "fields": {
                "type": {
                  "type": "stringFacet"
                }
              },
              "type": "document"
            }
          },
          "type": "document"
        },
        "rating_value": [
          {
            "type": "number"
          },
          {
            "type": "numberFacet"
          }
        ],
        "reviews": {
          "dynamic": true,
          "fields": {
            "comment": {
              "type": "string"
            },
            "rating": [
              {
                "type": "number"
              },
              {
                "type": "numberFacet"
              }
            ]
          },
          "type": "document"
        },
        "short-description": {
          "type": "string"
        },
        "specific_category": [
          {
            "type": "string"
          },
          {
            "type": "stringFacet"
          }
        ],
        "students": [
          {
            "type": "number"
          },
          {
            "type": "numberFacet"
          }
        ],
        "title": {
          "type": "string"
        }
      }
    }
  }
  ```

#### Facets configurados
- `currency`, `general_category`, `language`, `specific_category`: facets de texto para filtros de navegación.
- `price`, `rating_value`, `students`, `reviews.rating`: facets numéricos que permiten agrupar resultados por rangos.

#### Highlighting
- Las consultas `$search` incluyen `highlight` sobre `title`, `description`, `short-description` y `reviews.comment`, devolviendo coincidencias resaltadas (`searchHighlights`).

#### Verificación
1. **Mapping:** revisado en Atlas UI → Search Indexes → `default` → JSON.
2. **Facets:** consultas `$searchMeta` retornan buckets para categorías y rangos numéricos verificando los `stringFacet` y `numberFacet` definidos.
3. **Highlighting:** consultas `$search` en Data Explorer muestran texto marcado en los campos configurados, cumpliendo el requisito de resaltado.

</details>

### Configuración RabbitMQ
<details> 
  <summary>Desplegar información</summary>  
  
Es el sistema que sirve como intermediario para que los servicios se pasen mensajes y realizar sus funciones correspondientes. Permite que el controller, BeautifulSoup y Spacy Entity Extractor trabajen de forma asíncrona, equilibrada en caso de que haya más de un Spacy Entity Extractor y soportando reinicio en caso de que algun mensaje no se procese.  El pipeline utiliza 2 colas:

**- queue_parse**  
Es producida por el Controller y consumida por el BeautifulSoup.  Su propósito principal es notificar que hay archivos HTML nuevos o modificados en S3 que deben ser parseados.  

**- queue_entity**  
Es producida por el BeautifulSoup y consumida por el Spacy Entity Extractor.  Su propósito principal es notificar que hay archivos JSON procesados listos para extracción de entidades.  



</details>

### UI
<details> <summary>Desplegar información</summary>

#### Uso de la AI
<details> <summary>Desplegar información</summary>


</details>


</details>

### Rest API
<details> <summary>Desplegar información</summary>

#### Uso de la AI
<details> <summary>Desplegar información</summary>


</details>

</details>

</details>


# Conclusiones
  
<details>
  <summary>Desplegar información</summary> 

1. El Spark Processor centraliza la normalización del dataset en una sola ejecución hace en mayuscula textos, formatea fechas, genera resúmenes y construye relaciones basadas en entidades, dejando la colección documents lista para indexarse en Atlas Search.

2. Gracias al empaquetado de componentes como CronJob con imagen Docker parametizable por Helm, el componente puede reejecutarse de forma controlada ante nuevas ingestas sin afectar a otros microservicios.

3. La implementación del scraping permitió obtener datos actualizados de forma automatizada, asegurando la repetición, escalabilidad y adaptabilidad a distintos sitios web.

4. Se ganaron conocimientos prácticos sobre web scraping, manipulación de archivos, carga mediante CLI y buenas prácticas de registro de errores.

5. La forma en que se diseña el controller evita que se procesen archivos que ya están en la base de datos y no han cambiado, brindando ahorro de recursos y tiempo de procesamiento.

6. La utilización de Spacy logra identificar correctamente entidades importantes sobre los productos de cursos, brindando así una mejor organización de la información dentro de cada uno de los productos que se mostrarán

</details>

# Recomendaciones
  
<details>
  <summary>Desplegar información</summary> 

1. Uso de variables de entorno
Se recomienda centralizar la configuración del sistema mediante variables de entorno, lo cual facilita la mantenibilidad y portabilidad de la aplicación. Estas variables deben incluir, entre otros aspectos, las credenciales y parámetros de conexión a la base de datos, así como las direcciones y claves necesarias para el consumo de endpoints externos.

2. Añadir métricas y alertas simples (por ejemplo, contador de registros procesados y tiempo de ejecución) para detectar rápidamente anomalías en pipelines futuros y facilitar el monitoreo en producción.

3. Agregar un proceso de validación de los datos extraídos para asegurar calidad, eliminar duplicados y facilitar etapas de análisis.

4. Se recomienda implementar mejores prácticas de seguridad para el manejo de credenciales para evitar fallos en la seguridad del proyecto.

5. Se recomienda validar que los archivos HTML realmente contengan información para de esta manera evitar que el componenyte que los consume procese archivos innecesarios y mantener la calidad de los datos.

6. Se recomienda analizar bien el contexto en el que será utilizado el modelo Spacy, ya que este contiene modelos con diferentes caracteristicas, algunos consumen más memoria lo cual puede ser no tan factible cuando se tienen recursos limitados, otros son más ligeros pero tienen peor redimiento, por esto se requiere un analisis de cuál podría ser el más adecuado.

</details>

# Referencias
  
<details>
  <summary>Desplegar información</summary> 

https://spark.apache.org/docs/latest/api/python/index.html

https://www.mongodb.com/docs/spark-connector/current/

https://www.mongodb.com/products/platform/atlas-search

https://www.mongodb.com/docs/atlas/atlas-search/define-field-mappings/

https://www.mongodb.com/docs/atlas/atlas-search/facet/

https://www.mongodb.com/docs/atlas/atlas-search/highlighting/

https://thunderbit.com/es/blog/python-scraping-tutorial-for-beginners 

https://requests.readthedocs.io/en/latest/user/quickstart/#custom-headers 

https://pythones.net/archivos-en-python-crear-guardar-files/ 

https://stackoverflow.com/questions/20986631/how-can-i-scroll-a-web-page-using-selenium-webdriver-in-python 

https://www.selenium.dev/selenium/docs/api/java/org/openqa/selenium/By.html 

https://stackoverflow.com/questions/69315951/how-to-run-aws-s3-sync-command-concurrently-for-different-prefixes-using-python/69317895#69317895 

https://www.codecademy.com/article/python-subprocess-tutorial-master-run-and-popen-commands-with-examples 

https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html 

https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html  

https://spacy.io/models/es

https://spacy.io/usage/models

</details>

# Tabla de Estado
  
<details>
  <summary>Desplegar información</summary>  



| Componente | % Evaluación | Estado | Observaciones |
| --- | --- | --- | --- |
| Controller | 5 % | Implementado | Flujo de reconciliación y mensajería operativo. |
| Web Scraper | 15 % | Implementado | Dataset de ≥500 productos almacenado en S3. |
| Beautiful Soup Parser | 15 % | Implementado | Parsing HTML a JSON estable en despliegue de 2 réplicas. |
| spaCy Entity Extractor | 10 % | Implementado | Entidades entities generadas y persistidas en augmented/. |
| Spark Processor Job | 15 % | Implementado | Normalización completa y escritura en documents. |
| Configuración Firestore / Mongo Atlas Search / RabbitMQ | 10 % | Implementado | Servicios gestionados configurados y accesibles desde los microservicios. |
| UI y REST API | 20 % | Implementado | UI en Vercel con autenticación y consumo de API segura. |
