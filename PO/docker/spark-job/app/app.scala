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

object App {

  // ==================== TRANSFORMACIONES ====================

  /** Normaliza fechas de created/indexed y crea vista "dates" */
  def procesarFechas(spark: SparkSession): Unit = {
    spark.sql("""
      SELECT struct(created.* ,
                    date_format(to_timestamp(created.`date-time`, "yyyy-MM-dd'T'HH:mm:ss'Z'"), "MM-dd-yyyy") AS date) as created,
             struct(indexed.* ,
                    date_format(to_timestamp(indexed.`date-time`, "yyyy-MM-dd'T'HH:mm:ss'Z'"), "MM-dd-yyyy") AS date) as indexed,
             DOI
      FROM messages
    """).createOrReplaceTempView("dates")
  }

  /** Concatena nombres de autores y crea vista "autors" */
  def procesarAutores(spark: SparkSession): Unit = {
    spark.sql("""
      SELECT author,
             transform(author, a -> concat(a.family, ' , ', a.given)) AS autor_names,
             DOI
      FROM messages
    """).createOrReplaceTempView("autors")
  }

  /** Procesa títulos y referencias, genera vistas "titulos", "referencias" y "referencess" */
  def procesarTitulosReferencias(spark: SparkSession): Unit = {
    spark.sql("""
      SELECT lower(trim(DOI)) AS DOI,
             title[0] AS titulo
      FROM messages
      WHERE DOI IS NOT NULL
    """).createOrReplaceTempView("titulos")

    spark.sql("""
      SELECT lower(trim(m.DOI)) as DOIorg,
             lower(trim(ref.DOI)) AS DOIref
      FROM messages m
      LATERAL VIEW OUTER explode(m.reference) r as ref
      WHERE ref.DOI IS NOT NULL
    """).createOrReplaceTempView("referencias")

    spark.sql("""
      SELECT r.DOIorg,
             collect_set(t.titulo) AS reference_tittle
      FROM referencias r
      JOIN titulos t ON r.DOIref = t.DOI
      GROUP BY r.DOIorg
    """).createOrReplaceTempView("referencess")
  }

  // ==================== MAIN ====================

  def main(args: Array[String]): Unit = {
    // Crear SparkSession
    val spark = SparkSession.builder()
      .appName("PipelineArticulos")
      .getOrCreate()

    val sc = spark.sparkContext
    val sqlcontext = new org.apache.spark.sql.SQLContext(sc)

    // Variables de entorno para conexión a ES
    val esHost = sys.env("ELASTIC")
    val esPort = "9200"   // fijo
    val esUser = sys.env("ELASTIC_USER")
    val esPass = sys.env("ELASTIC_PASS")

    // Verificar si hay archivos en /data
    val dataPath = "/data"
    val filesExist = new File(dataPath).listFiles != null && new File(dataPath).listFiles.exists(_.isFile)

    if (filesExist) {
      // Leer JSON desde /data
      val df = spark.read.option("multiline", "true").json(dataPath)

      // Vista inicial
      df.createOrReplaceTempView("documents")
      spark.sql("SELECT message.* FROM documents").createOrReplaceTempView("messages")

      // ========== TRANSFORMACIONES ==========
      procesarFechas(spark)

      // Quitar created/indexed del JSON original
      val df2 = df.withColumn("message", col("message").dropFields("created", "indexed"))
      df2.createOrReplaceTempView("dfFormateado")

      procesarAutores(spark)
      procesarTitulosReferencias(spark)

      // Tabla messagesFinal unida con las vistas previas
      spark.sql("SELECT message.* FROM dfFormateado").createOrReplaceTempView("messagesFinal")

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

      // Reintegration final
      val dFinal = spark.sql("""
        SELECT 
            A.status,
            A.`message-type`,
            A.`message-version`,
            struct(B.*) AS message
        FROM dfFormateado AS A
        LEFT JOIN messagesFinal AS B
            ON A.message.DOI = B.DOI
      """)

      // Guardar en Elasticsearch
      dFinal.saveToEs("data", Map(
        "es.nodes" -> esHost,
        "es.port" -> esPort,
        "es.nodes.wan.only" -> "true",
        "es.net.http.auth.user" -> esUser,
        "es.net.http.auth.pass" -> esPass,
        "es.write.operation" -> "upsert",
        "es.mapping.id" -> "message.DOI"
      ))

      println("✅ Datos guardados en Elasticsearch correctamente")
    } else {
      println("⚠️ No se encontraron archivos en /data")
    }

    spark.stop()
  }
}