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


// Crear SparkSession
val spark = SparkSession.builder().getOrCreate()
val sc = spark.sparkContext
val sqlcontext = new org.apache.spark.sql.SQLContext(sc)

// Leer variables de entorno
val esHost = sys.env("ELASTIC")
val esPort = "9200"   // Puerto fijo
val esUser = sys.env("ELASTIC_USER")
val esPass = sys.env("ELASTIC_PASS")

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

//----------------------------TRANSFOMACION 3 -------------------------------------------------------


//FIN DE LAS Transformaciones

//Este contiene los campos de message a partir del documento formateado
spark.sql("SELECT message.* FROM dfFormateado").createOrReplaceTempView("messagesFinal")

//AQUI SE UNE LA ESTRUCTURA DE MESSAGES CON LOS NUEVOS CAMPOS
spark.sql("""
SELECT 
    A.*,
    B.created,
    B.indexed
FROM messagesFinal AS A
LEFT JOIN dates AS B
    ON A.DOI = B.DOI
""").createOrReplaceTempView("messagesFinal")

//SE REINTEGRA MESSAGES CON LOS DEMAS CAMPOS DEL JSON ORIGINAL GENERO UN NUEVO STRUCT PARA AGRUPAR TODOS LOS CAMPOS DE MESSAGES Y QUE SE VUELVA A ANIDAR EN MESSAGE COMO EL ORIGINAL
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

dFinal.show(false)
dFinal.printSchema()

// Guardar resultado en ES
dFinal.saveToEs("articulos", Map(
    "es.nodes" -> esHost,
    "es.port" -> esPort,
    "es.nodes.wan.only" -> "true",
    "es.net.http.auth.user" -> esUser,
    "es.net.http.auth.pass" -> esPass,
    "es.write.operation" -> "upsert",  // Inserta si no existe, sobreescribe si existe
    "es.mapping.id" -> "message.DOI"
))


println("Se guardaron los índices de prueba")
