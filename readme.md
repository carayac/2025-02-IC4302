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

  El web scraper es un pequeño código en python que se corre localmente fuera de kubernetes. Se encarga de recorrer la página de cursos online "edutin". Recorre las categorías "programacion", "cocina", "creativo", "salud", "negocio", "deporte", "psicologia", "ciencia", "cloud computing", "mantenimiento", "moda", "arte", "idiomas" y "marketing". Para esto, se usa selenium para hacer scroll en la página principal de edutin, y una vez que se hayan cargado suficientes cursos, se recupera el html de la página. Luego, se recorre el html en busca de la dirección que lleva a la información espcífica de cada curso. Cuando se encuentra, se extrae el html de esa dirección. Los html se descargan localmente en la carpeta "productos", y van numerados del 001 al 505. Una vez se han descargado los 505 cursos, estos se suben a la carpeta del bucket de aws, ic-tec-dataset/CARPETA_HCDCP/. Desde ahí se podrán recuperar los datos posteriormente.

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


</details>

### Configuración Firestore
<details> <summary>Desplegar información</summary>


</details>

### Configuración Mongo Atlas
<details> <summary>Desplegar información</summary>


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
