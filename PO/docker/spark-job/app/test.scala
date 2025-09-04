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
    // Filtra filas donde DOI sea "10.1126/science.adz6436"
    val dateValues = createdDates.filter(col("DOI") === "10.1126/science.adz6436")
    assert(dateValues.count() == 1, "No se encontró exactamente un registro con DOI '10.1126/science.adz6436'")
    
    // Verifica que las fechas coincidan con los valores esperados de "08-02-2025" en indexed.date
    val invalidindexed = dateValues.filter(col("indexed.date") =!= "08-02-2025")
    assert(invalidindexed.count() == 0, "La fecha 'indexed.date' no coincide con el valor esperado")
    // Verifica que las fechas coincidan con los valores esperados de "08-01-2025" en created.date
    val invalidCreated = dateValues.filter(col("created.date") =!= "07-31-2025")
    assert(invalidCreated.count() == 0, "La fecha 'created.date' no coincide con el valor esperado")

    //-----------------TRANSFORMACION 2-----------------
    //Validación de extracción de autores de la vista temporal 
    Functions.extractAuthors(spark)
    val createdAuthors = spark.sql("SELECT * FROM autors") 
    
    // Filtra filas donde DOI sea "10.1126/science.adz6436"
    val autorValues = createdAuthors.filter(col("DOI") === "10.1126/science.adz6436")
    assert(autorValues.count() == 1, "No se encontró exactamente un registro con DOI '10.1126/science.adz6436'")

    // Verifica que los autores coincidan con la lista esperada
    val autores = Array("Permar , Sallie R.", "Wilson , Patrick C.") 
    val invalidAuthors = autorValues.filter(
    sort_array(col("autor_names")) =!= sort_array(array(autores.map(lit): _*)))
    assert(invalidAuthors.count() == 0, "La lista de 'autor_names' no coincide con el valor esperado")

    //-----------------TRANSFORMACION 3-----------------
    //Validación de extracción de titulos de la vista temporal 
    Functions.extractTitlesAndReferences(spark)
    val createdTitles = spark.sql("SELECT * FROM referencess") 
    
    // Filtra filas donde DOI sea "10.1126/science.adz6436"
    val tittleValues = createdTitles.filter(col("DOIorg") === "10.1126/science.adz6436")
    assert(tittleValues.count() == 1, "No se encontró exactamente un registro con DOI '10.1126/science.adz6436'")

    // Verifica que los titulos referenciados coincidan con la lista esperada
    val titulos = Array("Strategies for HIV-1 vaccines that induce broadly neutralizing antibodies","Precise targeting of HIV broadly neutralizing antibody precursors in humans","Vaccination with mRNA-encoded nanoparticles drives early maturation of HIV bnAb precursors in humans")
    val invalidtittles = tittleValues.filter(
    sort_array(col("reference_tittle")) =!= sort_array(array(titulos.map(lit): _*)))
    assert(invalidtittles.count() == 0, "La lista de 'message.reference_tittle' no coincide con el valor esperado")

    sys.exit(0) // Salida 0 = tests OK

} catch {
    case e: Throwable =>
        println(s" Test falló: ${e.getMessage}")
        sys.exit(1) // Salida 1 = falla
}