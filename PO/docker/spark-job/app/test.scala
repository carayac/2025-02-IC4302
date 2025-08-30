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


val dataPath = "/data"
val filesExist = new File(dataPath).listFiles != null && new File(dataPath).listFiles.exists(_.isFile)

if (filesExist) {
    
    // Lee JSON desde /data
    val df = spark.read.option("multiline","true").json("/data")

    val dfFinal = Functions.processArticles(spark,df) //Llama a la función que procesa los artículos  

    //AQUI VA ASSERTS
} 
