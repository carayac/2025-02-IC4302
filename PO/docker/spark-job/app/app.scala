import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.SparkConf
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.SparkSession._
import org.elasticsearch.spark.sql
import org.elasticsearch.spark.sql._
import org.elasticsearch.spark._ 
import org.apache.spark.sql.functions._
import org.apache.spark.sql.Column //Esta libreria me permite hacer un dropFields por medio de columnas
import java.io.File //Esta libreria me permite verificar si existen archivos en el directorio /data


// Crea la SparkSession
val spark = SparkSession.builder().getOrCreate()
val sc = spark.sparkContext
val sqlcontext = new org.apache.spark.sql.SQLContext(sc)

// Lee las variables de entorno las cuales permiten la conexion a ES
// ELASTIC, ELASTIC_USER, ELASTIC_PASS
// ELASTIC es la IP o dominio de elasticsearch      
// ELASTIC_USER es el usuario
// ELASTIC_PASS es la contraseña    
// ELASTIC_PORT es el puerto, pero en este caso es fijo 9200

val esHost = sys.env("ELASTIC")
val esPort = "9200"   // Puerto fijo
val esUser = sys.env("ELASTIC_USER")
val esPass = sys.env("ELASTIC_PASS")


val dataPath = "/data"
val filesExist = new File(dataPath).listFiles != null && new File(dataPath).listFiles.exists(_.isFile)

if (filesExist) {
    
    // Leer JSON desde /data
    val df = spark.read.option("multiline","true").json("/data")


    //INICIO DE TRANSFORMACIONES

    //Creo una vista temporal de documento original
    df.createOrReplaceTempView("documents") //dataframe original

    spark.sql("SELECT message.* FROM documents").createOrReplaceTempView("messages") //tabla temporal que permite extraer la estructura a trabajar
    //spark.table("messages").printSchema() //veo el esquema

    //----------------------------TRANSFOMACION 1 -------------------------------------------------------


    //obtengo las columnas de fechas a partir de messages y creo una estrutura con el nuevo campo asi como con el doi para ser indentificadas al momento de hacer la union entre datos

    spark.sql("""SELECT struct(created.* , date_format(to_timestamp(created.`date-time`, "yyyy-MM-dd'T'HH:mm:ss'Z'"), "MM-dd-yyyy") AS date) as created, struct(indexed.* , date_format(to_timestamp(indexed.`date-time`, "yyyy-MM-dd'T'HH:mm:ss'Z'"), "MM-dd-yyyy") AS date) as indexed , DOI FROM messages""").createOrReplaceTempView("dates")

    //formateo el dataframe original para tener message solo con los campos necesarios y evitar repeticiones
    val df2 = df.withColumn("message", col("message").dropFields("created", "indexed"))
    df2.createOrReplaceTempView("dfFormateado")

    //----------------------------TRANSFOMACION 2 -------------------------------------------------------

    //Obtengo las columnas de autores a partir de messages
    spark.sql("""SELECT author, transform(author, a -> concat(a.family, ' , ', a.given)) AS autor_names, DOI FROM messages""").createOrReplaceTempView("autors")


    //----------------------------TRANSFOMACION 3 -------------------------------------------------------

    //Almaceno los doi y repsctivo tittle juntos
    spark.sql("""SELECT lower(trim(DOI)) AS DOI, title[0] AS titulo FROM messages WHERE DOI IS NOT NULL""").createOrReplaceTempView("titulos")

    //Obtengo el DOI de referencia unicamente en los que tienen
    //DOIorg corresponde al del articulo base, DOIref es de cada referencia 

    spark.sql("""SELECT lower(trim(m.DOI)) as DOIorg, lower(trim(ref.DOI)) AS DOIref FROM messages m LATERAL VIEW OUTER explode(m.reference) r as ref WHERE ref.DOI IS NOT NULL""").createOrReplaceTempView("referencias")

    //Se unen ambas tablas: titulos y referencias para conseguir un array con cada tittle
    spark.sql("""SELECT r.DOIorg, collect_set(t.titulo) AS reference_tittle FROM referencias r JOIN titulos t ON r.DOIref = t.DOI GROUP BY r.DOIorg """).createOrReplaceTempView("referencess")


    //FIN DE LAS Transformaciones

    //Este contiene los campos de message a partir del documento formateado
    spark.sql("SELECT message.* FROM dfFormateado").createOrReplaceTempView("messagesFinal")

    //AQUI SE UNE LA ESTRUCTURA DE MESSAGES CON LOS NUEVOS CAMPOS
    //Se unen todas las tablas temporales creadas anteriormente con messagesFinal
    //LEFT JOIN PARA QUE NO SE PIERDAN LOS REGISTROS QUE NO TIENEN DATOS EN LAS OTRAS TABLAS    
    //SE HACE UN LOWER Y TRIM A LOS DOIS PARA EVITAR PROBLEMAS DE UNION POR ESPACIOS O MAYUSCULAS
    spark.sql("""
    SELECT 
        A.*,
        B.created,
        B.indexed,
        C.autor_names,
        D.reference_tittle
    FROM messagesFinal AS A
    LEFT JOIN dates AS B ON A.DOI = B.DOI
    LEFT JOIN autors AS C ON A.DOI = C.DOI
    LEFT JOIN referencess AS D ON lower(trim(A.DOI)) = D.DOIorg
    """).createOrReplaceTempView("messagesFinal")

    //SE REINTEGRA MESSAGES CON LOS DEMAS CAMPOS DEL JSON ORIGINAL GENERO UN NUEVO STRUCT PARA AGRUPAR TODOS LOS CAMPOS DE MESSAGES Y QUE SE VUELVA A ANIDAR EN MESSAGE COMO EL ORIGINAL
    //SE HACE UN LEFT JOIN PARA NO PERDER REGISTROS
    val dFinal = spark.sql(""" SELECT 
        A.status,
        A.`message-type`,
        A.`message-version`,
        struct(B.*) AS message
    FROM dfFormateado AS A
    LEFT JOIN messagesFinal AS B
        ON A.message.DOI = B.DOI
    """)


    // UNION FINAL DE LOS NUEVOS CAMPOS TRANSFORMADOS A LA ESTRUCTURA DE message

    //dFinal.show(false)
    //dFinal.printSchema()

    // Guardar resultado en ES
    dFinal.saveToEs("data", Map(
    "es.nodes" -> esHost,
    "es.port" -> esPort,
    "es.nodes.wan.only" -> "true",
    "es.net.http.auth.user" -> esUser,
    "es.net.http.auth.pass" -> esPass,
    "es.write.operation" -> "upsert",  // Inserta si no existe, sobreescribe si existe
    "es.mapping.id" -> "message.DOI"
    ))
    //println("Se guardaron los índices de prueba")

} 

