# IC4302 - Proyecto 01: Semantify Book Reviews

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

#### 3.2 Configuracion de utilización de la aplicación web

Para la utilización de la aplicación web, se presentan dos opciones utilizar con Memcached o si este, para pdoer configurar su uso debe dirigirse a charts **-->** application-web **-->** values.yaml.  Si usted desea utilizar el backend con Memcached debe hailitar la opcion **useMemcached** en true, de lo contrario puede utilizarlo en false y se contruirá sin Memcached.  

> [!IMPORTANT]  
> La duracion de construccion de la imagen HuggingFace puede tardar unos minutos.

```yaml
config:
  docker_registry: SU_USUARIO
  backend:
    enabled: true
    replicas: 1
    name: backend-ui
    useMemcached: false #Variable para habilitar o deshabilitar Memcached
    image: backend-ui
    imageMemcached: backend-ui-memcached
  frontend:
    enabled: true
    replicas: 2
    name: frontend #this is the service name of frontend which represents the web application and the user interface
    image: frontend-ui   
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


# Pruebas Unitarias
  
<details>
  <summary>Desplegar información</summary> 
info
</details>


# Configuración de componenetes 
<details>
  <summary>Desplegar información</summary>  
  
A continuación se presenta un resumen de lo componentes aplicado en ekl proyecto  

## UI 
  <details>
  <summary>Desplegar información</summary>  
    
### Registro / Inicio de sesión
Se implementan dos pantallas, una para crear cuenta y otra para iniciar sesión. En el registro se validan los campos básicos nombre completo, correo, descripcion y contraseña.  Toda la información relacionada al cliente es guardado en MariaDB. 
En el inicio de sesión se toma el correo y la contraseña para la validación de existencia del usuario.
  
### Menú de navegación
  Al entrar, la persona podrá ver una barra de navegación para poder ingresar a cualquiera de las distincas opciones y navegar facilmente a cada función
  - Find Book
  - Search Prompts
  - Find Friends
  - Feed
  - Friends
  - Me
  
### Find Book
Para Find Book se presenta un campo de busqueda, donde el usuario escribe la necesidad de tipo de libros que desea buscar y con respecto a su petición podrá tener dos opciones: **Buscar** o **Publicar**
Al buscar podrá obtener resultados de ta ta ta en los que podrá conusltar información general de los libros obtenidos.  
Al utilizar la opcion de publicar, el prompt o petición del usuario será publicado en el feed para ser consultado en un futuro o para que sea visto por sus amigos. 
  
### Search Prompts
En Search Prompts se realiza una barra de búsqueda que filtra prompts por el texto y por el nombre de usuario. Cada tarjeta de prompt mostrada incluye la acción de “like”. Cuando el usuario da like, se realiza una actualización de likes en los prompts del usuario y ese prompt también se agrega al Feed del usuario que dio like. 
  
### Find Friends
Para Find Friends se construye un buscador por nombre. Cada resultado se presenta con un pequeño perfil con el nombre del usuarios y cantidad de followers, además de un botón de “Follow” para poder agregarlo a sus amigos.
  
### Feed
El Feed mezcla los prompts propios y los de la gente que el usuario sigue, ordenados del más reciente al más antiguo.   También al lado del prompt puede econctrar el botón de **buscar** de esta manera si el usuario quiere buscar los resultados que puede arrojar ese prompt lo puede hacer.

### Friends
La sección Friends lista a las personas que el usuario ya sigue, así como la opcion de dejarlos de seguir si así lo decide.
  
### Me
En Me se centralizan dos cosas: el perfil del usuario y la gestión de sus prompts. Para el perfil se muestra el nombre, apellido, descripción y correo.  Se permite editarlos.  
Para los prompts propios, se muestra una lista editable con opciones para modificar o borrar el prompt. La idea con esta funcionalidad es que el usuario tenga control total de su información y contenido de manera facil.  
Por último se presenta el botón de **logout** para cerrar sesión y redirigir a la pantalla de inicio de sesión

</details>  

</details>  





# Conclusiones
  
<details>
  <summary>Desplegar información</summary> 

  info

</details>

# Recomendaciones
  
<details>
  <summary>Desplegar información</summary> 

  info

</details>

# Referencias
  
<details>
  <summary>Desplegar información</summary> 


  https://huggingface.co/sentence-transformers/all-mpnet-base-v2

</details>

# Tabla de Estado
  
<details>
  <summary>Desplegar información</summary>  



| Componente                          | Estado        | Notas / Pendientes     |
|-------------------------------------|---------------|------------------------|
| Hugging Face API                    |               |                        |
| S3 Crawler Cron Job                 |               |                        |
| Ingest                              |               |                        |
| API                                 |               |                        |
| API con Memcached                   |               |                        |
| UI (Frontend)                       |               |                        |
| Base de Datos                       |               |                        |
| Observabilidad de componentes       |               |                        |
| Componentes automatizados           |               |                        |
| Pruebas (unitarias/integración)     |               |                        |


</details>

