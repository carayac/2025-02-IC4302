from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import initcap, col, expr, when, date_format,to_date , regexp_replace, udf, explode, collect_list, slice, array_contains, struct, monotonically_increasing_id, flatten, array_distinct, row_number, coalesce
from pyspark.sql.types import ArrayType, StructType, StringType, DateType, TimestampType
from pyspark.sql.window import Window
import logging
import sys
import os
import re



# Set up logging to output to stdout
logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

#Env variables
uri = os.getenv("URI_MONGODB")
input_path = os.getenv("VOLUMEN_PVC")


#creatre spark session with mongo conection to write
def createSession():
    """Crea una sesión Spark reutilizable"""
    spark = SparkSession.builder \
        .appName("spark-job") \
        .config("spark.executor.memory", os.getenv("SPARK_EXECUTOR_MEMORY", "2g")) \
        .config("spark.driver.memory", os.getenv("SPARK_DRIVER_MEMORY", "1g")) \
        .config("spark.sql.shuffle.partitions", os.getenv("SPARK_SQL_SHUFFLE_PARTITIONS", "16")) \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.mongodb.write.connection.uri", uri) \
        .getOrCreate()
    return spark

#read augmented data from json. This is a data volume
def read_augmented_data(spark, input_path):
    if not input_path:
        raise ValueError("VOLUMEN_PVC no definido; no se puede leer datos augmentados")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Ruta de datos {input_path} no existe")

    if os.path.isdir(input_path):
        if not any(entry for entry in os.scandir(input_path)):
            raise FileNotFoundError(f"Ruta de datos {input_path} no contiene archivos para procesar")

    df = spark.read.option("multiline","true").json(input_path)
    df.createOrReplaceTempView("augmented_data")
    logger.info("Augmented data loaded and registered as temporary view")
    return df


#Transformation #1
#Convert all text columns to start with uppercase
def uppercase_first_letter(dataframe):
    """Normaliza textos para que comiencen con mayúscula"""

    text_columns = [field.name for field in dataframe.schema.fields if field.dataType.simpleString() == 'string']
    
    for col_name in text_columns:
        dataframe = dataframe.withColumn(col_name, initcap(col(col_name)))


    logger.info("Text columns normalized to start with uppercase")
    return dataframe


#This function put the intial capital letter in nested struct and array of struct text fields for example entities and comments
def normalize_entities(dataframe):
    try:
        schema = dataframe.schema

        for field in schema.fields:
            fname = field.name
            ftype = field.dataType

            # Manage array<struct>
            if isinstance(ftype, ArrayType) and isinstance(ftype.elementType, StructType):
                elem_fields = ftype.elementType.fields
                parts = []
                for ef in elem_fields:
                    ename = ef.name
                    if isinstance(ef.dataType, StringType):
                        parts.append(f"'{ename}', initcap(x.{ename})")
                    else:
                        parts.append(f"'{ename}', x.{ename}")

                named = ', '.join(parts)
                transformed = expr(f"transform({fname}, x -> named_struct({named}))")
                dataframe = dataframe.withColumn(fname, when(col(fname).isNotNull(), transformed).otherwise(col(fname)))

            # Manage array<string> (ej. "caracteristicas")
            elif isinstance(ftype, ArrayType) and isinstance(ftype.elementType, StringType):
                transformed = expr(f"transform({fname}, x -> initcap(x))")
                dataframe = dataframe.withColumn(fname, when(col(fname).isNotNull(), transformed).otherwise(col(fname)))

            # Manage struct 
            elif isinstance(ftype, StructType):
                parts = []
                for sf in ftype.fields:
                    sname = sf.name
                    if isinstance(sf.dataType, StringType):
                        parts.append(f"'{sname}', initcap({fname}.{sname})")
                    else:
                        parts.append(f"'{sname}', {fname}.{sname}")

                named = ', '.join(parts)
                transformed = expr(f"named_struct({named})")
                dataframe = dataframe.withColumn(fname, when(col(fname).isNotNull(), transformed).otherwise(col(fname)))

        logger.info("Nested struct/array text fields normalized")
    except Exception:
        logger.exception("Error al normalizar entidades/comentarios anidados")

    return dataframe


# Transformation #2
# Format dates to DD/MM/YYYY throughout the schema using Spark SQL
def format_dates_ddmmyyyy_sql(dataframe):
    parsed_primary = to_date(col("date_extracted"), "dd/MM/yyyy")
    parsed_iso = to_date(col("date_extracted"), "yyyy-MM-dd")
    parsed_slash_iso = to_date(col("date_extracted"), "yyyy/MM/dd")
    parsed_mixed = to_date(regexp_replace(col("date_extracted"), "/", "-"), "dd-MM-yyyy")

    df_formatted = dataframe.withColumn(
        "date_extracted",
        date_format(
            coalesce(parsed_primary, parsed_iso, parsed_slash_iso, parsed_mixed),
            "dd/MM/yyyy"
        )
    )
    logger.info("Date fields formatted to DD/MM/YYYY")
    return df_formatted

# Transformation #3
# Generate short summary using TF-IDF
# Summary helper that trims text to max_len preserving whole words
def resumen_simple(texto, max_len=140):
    if not texto:
        return ""
    
    texto = texto.strip()
    if len(texto) <= max_len:
        return texto

    snippet = texto[: max_len + 1]
    last_space = snippet.rfind(" ")

    if last_space == -1:
        return texto[:max_len].rstrip() + "..."

    return snippet[:last_space].rstrip() + "..."

# converte to UDF in Spark
resumen_udf = udf(resumen_simple, StringType())

#main function to add summary column
def summary(dataframe):
    return dataframe.withColumn("short-description", resumen_udf(col("description")))

# Transformation #4
# Add related products based on entities
def add_related_products(df, max_relacionados: int = 10) -> DataFrame:
    if "entities" not in df.columns:
        logger.warning("Entities column missing; skipping related products enrichment")
        return df

    # 1. Add internal id to identify products and avoid self-matching
    df_with_id = df.withColumn("_product_id", monotonically_increasing_id())

    # Build global mapping: for every product/entity produce (entity_text, full_product)
    product_struct_cols = [col(c) for c in df.columns] + [col("_product_id")]
    full_struct = struct(*product_struct_cols).alias("full_product")

    exploded_global = df_with_id.withColumn("entity", explode(col("entities"))) \
                               .withColumn("entity_value", col("entity.value")) \
                               .withColumn("entity_type", col("entity.type")) \
                               .filter(col("entity_value").isNotNull()) \
                               .select(col("entity_value"), col("_product_id"), full_struct)

    # limit number of products por entidad antes del collect_list para evitar OOM
    max_por_entidad = max_relacionados * 5
    entity_window = Window.partitionBy("entity_value").orderBy(col("_product_id"))
    limited_global = exploded_global.withColumn("_entity_rank", row_number().over(entity_window)) \
                                     .filter(col("_entity_rank") <= max_por_entidad) \
                                     .drop("_entity_rank")

    df_grouped = limited_global.groupBy("entity_value").agg(collect_list(col("full_product")).alias("related_per_entity"))

    # For each product, explode its entities and join to the grouped related list, then aggregate back
    left_exploded = df_with_id.select("_product_id", "entities") \
                             .withColumn("entity", explode(col("entities"))) \
                             .withColumn("entity_value", col("entity.value")) \
                             .filter(col("entity_value").isNotNull()) \
                             .select("_product_id", "entity_value")

    joined = left_exploded.join(df_grouped, on="entity_value", how="left")

    # Aggregate per product id into array<array<struct>> then flatten
    agg = joined.groupBy("_product_id").agg(collect_list(col("related_per_entity")).alias("related_lists")) \
                .withColumn("related_flat", flatten(col("related_lists")))

    # Exclude self (by matching _product_id inside struct), deduplicate by titulo and limit
    # the full_struct included _product_id as a field named '_product_id'
    agg = agg.withColumn(
        "productos_relacionados",
        expr("slice(array_distinct(filter(related_flat, x -> x._product_id IS NOT NULL AND x._product_id <> _product_id)), 1, %d)" % max_relacionados)
    )

    # Join back to original dataframe on _product_id and select original cols + productos_relacionados
    df_final = df_with_id.join(agg.select("_product_id", "productos_relacionados"), on="_product_id", how="left")

    # Remove internal id column and keep original ordering of columns
    original_cols = [col(c) for c in df.columns]
    df_final = df_final.select(*original_cols, col("productos_relacionados"))

    logger.info("Related products added based on entities, excluding self and deduplicated")
    return df_final

# Main normalization pipeline using Spark SQL
def normalize_data(spark):
    """
    Pipeline completo de normalización usando Spark SQL:
    1.1 Verificar que las cadenas de texto comiencen con mayúscula
    1.2 Verificar y normalizar textos en campos anidados (Comiencen en mayuscula) estos son las entities y los comentarios
    2. Verificar el formato de fechas a DD/MM/YYYY en todo el esquema
    3. Generar resumen corto usando TF-IDF
    4. Agregar productos relacionados basados en entidades
    """
    # Transformation 1 convierte all text to start with uppercase
    df = spark.sql("SELECT * FROM augmented_data")
    df = uppercase_first_letter(df)

    # Normalice nested struct and array text fields with uppercase first letter
    df = normalize_entities(df)

    # Formate dates to DD/MM/YYYY throughout the schema
    #if use the sql version to apply the format throughout the schema
    df = format_dates_ddmmyyyy_sql(df)

    #genereate the short version of the description
    df = summary(df)
    #create temp view again TO see the new column in sql
    df.createOrReplaceTempView("productos")
    #add related products
    df = add_related_products(df)
    
    logger.info("Data normalization completed")
    return df

#Function to save to mongodb 
def save_to_mongodb(df):
    """
    Guarda DataFrame en MongoDB Atlas.
    Requiere configuración de spark.mongodb.output.uri
    """
    df.write \
        .format("mongodb") \
        .mode("overwrite") \
        .option("uri", uri) \
        .save()
    logger.info("Datos procesados guardados en MongoDB Atlas")

#main execute function
def execute():
    #global session function for the cronjob to use spark
    spark = None
    try:
        spark = createSession()

        # read the augmented data in the pvc
        read_augmented_data(spark, input_path)
        # execute the normalization pipeline
        normalized_df = normalize_data(spark)

        # save to MongoDB Atlas
        save_to_mongodb(normalized_df)
        logger.info("Normalización completada y datos guardados en MongoDB")
    except Exception:
        logger.exception("Error durante la ejecución del pipeline de Spark")
    finally:
        if spark is not None:
            spark.stop()
