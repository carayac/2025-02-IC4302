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
    
    // Lee JSON desde /data
    val df = spark.read.option("multiline","true").json("/data")

    val dfFinal = Functions.processArticles(spark,df) //Llama a la función que procesa los artículos  

    // Guardar resultado en ES
    dfFinal.saveToEs("data", Map(
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
