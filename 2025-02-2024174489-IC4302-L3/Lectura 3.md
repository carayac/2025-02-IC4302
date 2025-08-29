# Vector Database   

## 1. En términos simples, ¿cuál es la principal diferencia entre las consultas en una base de datos de vectores y bases de datos relacionales?

La principal diferencia es que en una base de datos relacional las consultas son estructuradas y buscan datos específicos en tablas, mientras que en una base de datos de vectores las consultas buscan similitudes entre vectores, osea, datos que se parezcan al vector de consulta, como imágenes o textos

## 2. ¿Cómo se diferencia la representación de datos en una base de datos de vectores con bases de datos SQL y NoSQL?

La diferencia es que en una base de datos de vectores los datos se representan como vectores de alta dimensión, que capturan características complejas pero no son legibles por humanos. En cambio, en bases de datos SQL los datos son números, cadenas o tiempos organizados en tablas y columnas con significado claro, mientras que en NoSQL los datos pueden no ser tan estructuruados, pero todavía resultan más comprensibles que los vectores

## 3. ¿Qué es un vector embedding o feature vector?

Un vector embedding o feature vector es la representación numérica de datos transformados en un vector de alta dimensión que captura relaciones o patrones importantes. Este vector se almacena junto con un identificador, metadatos y, en algunos casos, el dato original, lo que permite describir y trabajar con información compleja

## 4. Explique el concepto de similarity search.

El similarity search es la base de las operaciones en bases de datos de vectores. Consiste en comparar vectores de alta dimensión que representan datos complejos (texto, imágenes, audio, video, etc.) para encontrar aquellos que son más parecidos entre sí. Estas busquedas se suelen hacer por medio de métodos la distancia Euclidiana, similitud de cosenos, producto punto y similitud de Jaccardcomo 

## 5. Explique los diferentes use cases para los que se pueden utilizar bases de datos de vectores.

- **Uso general**: Cualquier dato que pueda representarse en vectores puede usarse para búsquedas de similitud, como estructuras moleculares, apartamentos en renta, colorización automática de imágenes, reconocimiento de expresiones faciales, seguimiento de activos digitales o sistemas de recomendación

- **Imágenes y videos**: Las imágenes se normalizan y extraen características que luego se vectorizan. Esto permite búsquedas de similitud y búsquedas inversas de imágenes. En videos, se trabaja con fotogramas, extrayendo sus características y considerando además la secuencia temporal, que se guarda como un tensor convertido en vector

- **Reconocimiento de voz**: El audio se convierte en digital, se divide en pequeños segmentos y se transforma en vectores. Esto se aplica tanto en autenticación de usuarios como en asistentes conversacionales, donde los vectores alimentan redes neuronales que reconocen y clasifican palabras

- **Chatbots y memoria a largo plazo**: Las bases de datos vectoriales pueden usarse como memoria externa de modelos generativos. Ayudan a superar limitaciones de recordar contextos largos en conversaciones, almacenando representaciones vectoriales para recuperar información pasada de manera más precisa
