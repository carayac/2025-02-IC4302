# Apuntes de Clase

En esta clase se explico el proyecto 2, por lo tanto se hara un resumen sobre esta evaluación

- La parte 1 del proyecto es constuir un **dataset**, este va a estar basado en un sitio de e-commerce.  

- Se va a usar algo llamado **seleniun webdriver**, este es un software que simula acciones, por ejemplo abrir el navejador, buscar un sitio de comida y entrar a la pagina que salga. Uno debe especificarle cual es el driver que va a usar, osea el web driver. Por lo tanto, uno le debe de indicar la url, que buscar y que hacer.

![1760746380979](image/Apuntes4/1760746380979.png)

- Por lo tanto con este seleniun webdrive, vamos hacer que  ingrese a una url y obtenga la informacion. Y con esa información es con la que se va a realizar nuestro dataset. Hay que elegir bien la pagina, ya que algunas tiene mayor seguridad y de vez en cuando mandan  **captcha**, esto es justo un mecanismo de seguridad que los sitios web usan para verificar que quien interactúa con ellos es un humano y no un bot.

- Este proceso se llama **web scraping**, toda esta informacion la vamos almacenar en el bucket que se trabajo en el proyecto 1

- Luego con un controller listamos los datos desde el bucket y los mandamos uno por uno a una coleccion a MongoDB Atlas. Se debe de verificar, si el dato ya existe o si esta distinto al anterior. 

- Se debe utilizar un **parser** de html en python para procesarlo con el titulo, caracteristicas y asi. A esto se le llama extraer los datos

- Una vez que se parsearon todos los html, se guardan como JSON en el PVC

- Luego usamos **spaCy**, este es un modelo de procesamiento de texto. Se va a procesar un texto y va a obtener una descripcion de cada palabra que proceso. Con esta información aumentamos aun más los datos. Esto lo gurdamos tambien en el PVC

![1760748409261](image/Apuntes4/1760748409261.png)

- Luego con Spark normalizamos esta información 

- En Mongo al **Atlas Search** le debemos crear un mapping

- Para la generacion del sitio web, tenemos permiso a utilizar **Inteligencia Artifical**, pero con la condición de explicar los prompts y documentar bien el código

- Se va a usar **Vercel**, ya que es muy facil su uso mediante github ya que es muy facil desplegarlo y los cambios se hacen automatico conlos push en github

- Se debe usar **React, Vite y TailwindCSS** para la creacion de la UI

- Se va a usar **Firebase** para el manejo de los usuarios

![1760748509899](image/Apuntes4/1760748509899.png)

- Se va a necesitar una API, para algunas llamadas que se deben de realziar. Esta se va hacer en **NodeJS**

- Toda este web, debe ser pública, es decir debe estar desplegada y poder ser accedida desde un link

![1760748334606](image/Apuntes4/1760748334606.png)
