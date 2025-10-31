from pyspark.sql import SparkSession
from pyspark.sql.functions import initcap, col, expr, when, date_format
from pyspark.sql.types import ArrayType, StructType, StringType, DateType, TimestampType
import logging
import sys
import os

# Set up logging to output to stdout
logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

uri = "mongodb+srv://dbUser:B1b5xCdAOZDVfjcC@productssearch.sao2plc.mongodb.net/ecomm.documents?appName=ProductsSearch"

def createSession():
    """Crea una sesión Spark reutilizable"""
    spark = SparkSession.builder \
        .appName("spark-job") \
        .config("spark.mongodb.write.connection.uri", uri) \
        .getOrCreate()
    return spark


def read_augmented_data(spark, input_path):
    """Lee datos augmented desde JSON y registra como tabla temporal"""
    df = spark.read.option("multiline","true").json(input_path)
    df.createOrReplaceTempView("augmented_data")
    return df


def uppercase_first_letter(dataframe):
    """Normaliza textos para que comiencen con mayúscula"""

    text_columns = [field.name for field in dataframe.schema.fields if field.dataType.simpleString() == 'string']
    
    for col_name in text_columns:
        dataframe = dataframe.withColumn(col_name, initcap(col(col_name)))


    logger.info("Text columns normalized to start with uppercase")
    return dataframe



def normalize_entities(dataframe):
    """Normaliza textos dentro de estructuras anidadas.

    - Recorre el esquema y para cada columna que sea ArrayType(StructType) o StructType
      aplica initcap a los campos de tipo string dentro del struct.
    - Preserva los campos no-texto.
    """
    try:
        schema = dataframe.schema

        for field in schema.fields:
            fname = field.name
            ftype = field.dataType

            # Manejar array<struct>
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

            # Manejar array<string> (ej. "caracteristicas")
            elif isinstance(ftype, ArrayType) and isinstance(ftype.elementType, StringType):
                transformed = expr(f"transform({fname}, x -> initcap(x))")
                dataframe = dataframe.withColumn(fname, when(col(fname).isNotNull(), transformed).otherwise(col(fname)))

            # Manejar struct directo
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


def format_dates_ddmmyyyy_sql(dataframe):
    spark = dataframe.sparkSession
    dataframe.createOrReplaceTempView("__tmp_format_dates")

    def sel(colname, dtype):
        q = f"`{colname}`"
        if isinstance(dtype, (DateType, TimestampType)):
            return f"date_format({q}, 'dd/MM/yyyy') as {q}"
        if isinstance(dtype, StringType):
            return (
                f"CASE WHEN to_date({q}, 'yyyy-MM-dd') IS NOT NULL THEN date_format(to_date({q}, 'yyyy-MM-dd'),'dd/MM/yyyy') "
                f"WHEN to_date({q}, 'dd/MM/yyyy') IS NOT NULL THEN date_format(to_date({q}, 'dd/MM/yyyy'),'dd/MM/yyyy') "
                f"ELSE initcap({q}) END as {q}"
            )
        if isinstance(dtype, ArrayType) and isinstance(dtype.elementType, StringType):
            return f"transform({q}, x -> CASE WHEN to_date(x,'yyyy-MM-dd') IS NOT NULL THEN date_format(to_date(x,'yyyy-MM-dd'),'dd/MM/yyyy') WHEN to_date(x,'dd/MM/yyyy') IS NOT NULL THEN date_format(to_date(x,'dd/MM/yyyy'),'dd/MM/yyyy') ELSE initcap(x) END) as {q}"
        if isinstance(dtype, ArrayType) and isinstance(dtype.elementType, StructType):
            parts = []
            for f in dtype.elementType.fields:
                if isinstance(f.dataType, (DateType, TimestampType)):
                    parts.append(f"'{f.name}', date_format(x.{f.name}, 'dd/MM/yyyy')")
                elif isinstance(f.dataType, StringType):
                    parts.append(
                        f"'{f.name}', CASE WHEN to_date(x.{f.name}, 'yyyy-MM-dd') IS NOT NULL THEN date_format(to_date(x.{f.name}, 'yyyy-MM-dd'),'dd/MM/yyyy') WHEN to_date(x.{f.name}, 'dd/MM/yyyy') IS NOT NULL THEN date_format(to_date(x.{f.name}, 'dd/MM/yyyy'),'dd/MM/yyyy') ELSE initcap(x.{f.name}) END"
                    )
                else:
                    parts.append(f"'{f.name}', x.{f.name}")
            return f"transform({q}, x -> named_struct({', '.join(parts)})) as {q}"
        if isinstance(dtype, StructType):
            parts = []
            for f in dtype.fields:
                if isinstance(f.dataType, (DateType, TimestampType)):
                    parts.append(f"'{f.name}', date_format({q}.{f.name}, 'dd/MM/yyyy')")
                elif isinstance(f.dataType, StringType):
                    parts.append(
                        f"'{f.name}', CASE WHEN to_date({q}.{f.name}, 'yyyy-MM-dd') IS NOT NULL THEN date_format(to_date({q}.{f.name}, 'yyyy-MM-dd'),'dd/MM/yyyy') WHEN to_date({q}.{f.name}, 'dd/MM/yyyy') IS NOT NULL THEN date_format(to_date({q}.{f.name}, 'dd/MM/yyyy'),'dd/MM/yyyy') ELSE initcap({q}.{f.name}) END"
                    )
                else:
                    parts.append(f"'{f.name}', {q}.{f.name}")
            return f"named_struct({', '.join(parts)}) as {q}"
        return f"{q}"

    select_list = [sel(f.name, f.dataType) for f in dataframe.schema.fields]
    sql = f"SELECT {', '.join(select_list)} FROM __tmp_format_dates"
    return spark.sql(sql)


def normalize_data(spark):
    """
    Pipeline completo de normalización usando Spark SQL:
    1. Extraer entidades normalizadas
    2. Añadir productos relacionados
    3. Normalizar textos con mayúscula inicial
    4. Normalizar fechas a DD/MM/YYYY
    5. Generar descripción corta (140 chars)
    """
    #1 Convertir todos los textos para que comiencen con mayúscula
    df = spark.sql("SELECT * FROM augmented_data")
    df = uppercase_first_letter(df)

    # 2 Normalizar textos en campos anidados
    df = normalize_entities(df)

    # 3 Formatear fechas a DD/MM/YYYY en todo el esquema
    # Usamos la versión basada en Spark SQL para aplicar el formato a todo el esquema
    #df = format_dates_ddmmyyyy_sql(df)

    logger.info("Data normalization completed")
    return df


def save_to_mongodb(df):
    """
    Guarda DataFrame en MongoDB Atlas.
    Requiere configuración de spark.mongodb.output.uri
    """
    df.write \
        .format("mongodb") \
        .mode("append") \
        .option("uri", uri) \
        .save()

def save_processed_data(df, output_path):
    """Guarda DataFrame procesado en JSON"""
    df.write.mode("overwrite").json(output_path)


def execute():

    """Función principal del CronJob"""
    spark = createSession()
    
    # Paths (ajustar según tu estructura)
    input_path = "/app/data"  # Carpeta augmented
    
    # Leer datos y registrar como tabla temporal
    read_augmented_data(spark, input_path)
    df = spark.sql("SELECT * FROM augmented_data")
    # Ejecutar pipeline de normalización (todo con Spark SQL)
    normalized_df = normalize_data(spark)
    
    # Guardar en MongoDB Atlas
    save_to_mongodb(normalized_df)

    # Opcional: guardar JSON local para debug
    save_processed_data(normalized_df, "/app/examples/processed")

    logger.info("Datos procesados guardados en MongoDB Atlas")
    
    spark.stop()
    logger.info("SNormalización completada y datos guardados en MongoDB")
