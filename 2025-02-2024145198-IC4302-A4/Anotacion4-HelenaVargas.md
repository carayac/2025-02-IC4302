	Bases de Datos II
	Helena Vargas
	II Sem 2025
## Anotaciones 24-10-25

# Indexar

## ¿Qué paso con Amazon?

Aunque hubo una caida de servicios por unas horas, no se cayeron todos los servicios porque tienen distintas availability zones, que están cercanas a los usuarios. Solo unos pocos clientes se vieron afectados, y además hay bases de datos multiregion, por lo que las bases de datos se replican en otras regiones, entonces no se pierde nada de información.

Si se usan servicios multiregion, son un poco más lentos y caros. Pero en una sola región, son más rápidos pero menos available.

El SLA de Amazon es 99.95%, así que como se cayó por 3 horas deben pagar 10% a los usuarios afectados. 


## Archivos de datos
Se tiene registros de tamaño fijo que son del mismo tamaño. 
Se tiene un puntero a archivos borrados, para ver si se pueden utilizar los espacios.

Al borrar datos, desde el punto de vista del file system, el archivo sigue pesando lo mismo. Solo pesa menos de manera lógica. 

En las bases de datos para evitar problemas de seguridad se hace un borrado de bajo nivel.

Se hace defragmentación con datos borrados, utilizando el espacio, sobreescribiendo por un archivo que sí tenga datos. Así al final del archivo queda todo el espacio. Esto se hace cuando quedan huecos en un archivo.

**Registros variables**: Sí causan problemas a diferencia de los fijos, que no causan problema de defragmentación porque tienen el mismo tamaño. 

Se tiene que hacer una conversión entre registros fijos y variables. Cuando no todos tienen el mismo tamaño, va leyendo unos pocos bytes para saber el tamaño y hacer los desplazamientos. 

En registros de tamaño fijo el scan puede ser más complicado, porque la búsqueda es más cara. 

![imagen1](graf1.png)


Tambien se puede ver la defragmentacion.

![imagen2](graf2.png)

Las bases de datos siempre tienen object storage. Se almacenan datos de tamaño binario. 

Cuando se hacen captcha, se enseña a las IA a reconocer caracteres. 

Con OCR se saca la información de texto.
