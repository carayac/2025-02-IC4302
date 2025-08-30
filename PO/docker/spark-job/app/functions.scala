import org.apache.spark.sql.{DataFrame, SparkSession}
import org.apache.spark.sql.functions._

object Functions {

    // Extrae las fechas de created e indexed y las formatea a MM-dd-yyyy
  def extractDates(spark: SparkSession): Unit = {
    spark.sql(
      """SELECT 
           struct(created.* , date_format(to_timestamp(created.`date-time`, "yyyy-MM-dd'T'HH:mm:ss'Z'"), "MM-dd-yyyy") AS date) as created, 
           struct(indexed.* , date_format(to_timestamp(indexed.`date-time`, "yyyy-MM-dd'T'HH:mm:ss'Z'"), "MM-dd-yyyy") AS date) as indexed , 
           DOI 
         FROM messages"""
    ).createOrReplaceTempView("dates") // Crea una vista temporal llamada "dates"
  }
    // Formatea el DataFrame eliminando las columnas created e indexed del struct message
  def formatDf(df: DataFrame): DataFrame = {
    val df2 = df.withColumn("message", col("message").dropFields("created", "indexed"))
    df2.createOrReplaceTempView("dfFormateado")
    df2// Retorna el DataFrame formateado
  }

  def extractAuthors(spark: SparkSession): Unit = {
    spark.sql(
      """SELECT author, 
                transform(author, a -> concat(a.family, ' , ', a.given)) AS autor_names, 
                DOI 
         FROM messages"""
    ).createOrReplaceTempView("autors")
  }

  def extractTitlesAndReferences(spark: SparkSession): Unit = {
    spark.sql(
      """SELECT lower(trim(DOI)) AS DOI, title[0] AS titulo 
         FROM messages 
         WHERE DOI IS NOT NULL"""
    ).createOrReplaceTempView("titulos")

    spark.sql(
      """SELECT lower(trim(m.DOI)) as DOIorg, 
                lower(trim(ref.DOI)) AS DOIref 
         FROM messages m 
         LATERAL VIEW OUTER explode(m.reference) r as ref 
         WHERE ref.DOI IS NOT NULL"""
    ).createOrReplaceTempView("referencias")

    spark.sql(
      """SELECT r.DOIorg, 
                collect_set(t.titulo) AS reference_tittle 
         FROM referencias r 
         JOIN titulos t ON r.DOIref = t.DOI 
         GROUP BY r.DOIorg"""
    ).createOrReplaceTempView("referencess")
  }
// Une todas las vistas temporales en una sola vista llamada messagesFinal representando el nodo message transformado
  def joinAll(spark: SparkSession): Unit = {
    spark.sql("SELECT message.* FROM dfFormateado").createOrReplaceTempView("messagesFinal")

    spark.sql(
      """SELECT 
           A.*,
           B.created,
           B.indexed,
           C.autor_names,
           D.reference_tittle
         FROM messagesFinal AS A
         LEFT JOIN dates AS B ON A.DOI = B.DOI
         LEFT JOIN autors AS C ON A.DOI = C.DOI
         LEFT JOIN referencess AS D ON lower(trim(A.DOI)) = D.DOIorg"""
    ).createOrReplaceTempView("messagesFinal") // Sobrescribe la vista messagesFinal con los nuevos datos
  }
// Construye el DataFrame final con la estructura requerida los campos status, message-type, message-version y message
  def buildFinalDf(spark: SparkSession): DataFrame = {
    spark.sql(
      """ SELECT 
           A.status,
           A.`message-type`,
           A.`message-version`,
           struct(B.*) AS message
         FROM dfFormateado AS A
         LEFT JOIN messagesFinal AS B
            ON A.message.DOI = B.DOI"""
    )
  }

  def processArticles(spark: SparkSession, df: DataFrame): DataFrame = {
    // Vista main
    df.createOrReplaceTempView("documents")
    spark.sql("SELECT message.* FROM documents").createOrReplaceTempView("messages")

    //Transformacion 1 extrae las fechas
    extractDates(spark)

    //Formatea el df para arugapar sobre el
    formatDf(df)

    //Transformacion 2 crea los autores
    extractAuthors(spark)

    //Transformacion 3 genera los titulos de referencias
    extractTitlesAndReferences(spark)

    //une los campos json originales con los campos 
    joinAll(spark)

    //construye df final
    buildFinalDf(spark)
  }
}
