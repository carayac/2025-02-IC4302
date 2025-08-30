import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.SparkConf
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.SparkSession._

// Crea la SparkSession
val spark = SparkSession.builder().getOrCreate()
val sc = spark.sparkContext
val sqlcontext = new org.apache.spark.sql.SQLContext(sc)

// Lee JSON desde /data
val df = spark.read.option("multiline","true").json("data/*.json")

//Ejecucion general de el procesamiento
//val dfFinal = Functions.processArticles(spark,df) //Llama a la función que procesa los artículos

try {
    assert(df != null, "La función processArticles devolvió un DataFrame nulo") // Verifica que el DataFrame no sea nulo
    val dfFinal = Functions.processArticles(spark,df) //Llama a la función que procesa los artículos

    //Validacion de DataFrame formateado
    val dfFormateado = Functions.formatDf(df)
    assert(dfFormateado.columns.contains("message"), "El DataFrame formateado no contiene la columna 'message'")
    assert(!dfFormateado.columns.contains("created"), "El DataFrame formateado contiene la columna 'created'")
    assert(!dfFormateado.columns.contains("indexed"), "El DataFrame formateado contiene la columna 'indexed'")

    //-----------------TRANSFORMACION 1-----------------
    //Validacion de extraccion de fechas
    Functions.extractDates(spark)
    val createdDates = spark.sql("SELECT * FROM dates")
    // Filtra filas donde DOI sea "10.1126/science.ady0241"
    val dateValues = createdDates.filter(col("DOI") === "10.1126/science.ady0241")
    assert(dateValues.count() == 1, "No se encontró exactamente un registro con DOI '10.1126/science.ady0241'")
    
    // Verifica que las fechas coincidan con los valores esperados de "08-02-2025" en indexed.date
    val invalidindexed = dateValues.filter(col("indexed.date") =!= "08-02-2025")
    assert(invalidindexed.count() == 0, "La fecha 'indexed.date' no coincide con el valor esperado")
    // Verifica que las fechas coincidan con los valores esperados de "08-01-2025" en created.date
    val invalidCreated = dateValues.filter(col("created.date") =!= "07-31-2025")
    assert(invalidCreated.count() == 0, "La fecha 'created.date' no coincide con el valor esperado")

    

    sys.exit(0) // Salida 0 = tests OK

} catch {
    case e: Throwable =>
        println(s" Test falló: ${e.getMessage}")
        sys.exit(1) // Salida 1 = falla
}