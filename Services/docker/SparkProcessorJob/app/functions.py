from ast import expr, date_format
from pyspark.sql import SparkSession


def createSession(app_name="Spark Processor Job"):
    """Crea una sesión Spark reutilizable"""
    spark = SparkSession.builder \
        .appName(app_name) \
        .config("spark.mongodb.output.uri", "mongodb://atlas-connection-string") \
        .getOrCreate()
    return spark


def read_augmented_data(spark, input_path):
    """Lee datos augmented desde JSON y registra como tabla temporal"""
    df = spark.read.json(input_path)
    df.createOrReplaceTempView("augmented_data")
    return df


def extract_normalized_entities(spark):
    """
    Extrae textos de entidades y los normaliza (lowercase, trim).
    Crea columna 'entity_texts' como array de strings.
    """
    query = """
    SELECT 
        *,
        CASE 
            WHEN entities IS NOT NULL THEN 
                TRANSFORM(entities, e -> LOWER(TRIM(e.texto)))
            ELSE 
                ARRAY()
        END AS entity_texts
    FROM augmented_data
    """
    df = spark.sql(query)
    df.createOrReplaceTempView("data_with_entities")
    return df


def get_related_products(spark, max_related=10):
    """
    Encuentra productos relacionados por entidades compartidas usando Spark SQL.
    """
    # Paso 1: Explotar entidades
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW exploded_entities AS
        SELECT 
            titulo AS product_id,
            titulo,
            entity_text
        FROM data_with_entities
        LATERAL VIEW EXPLODE(entity_texts) AS entity_text
        WHERE entity_text IS NOT NULL
    """)
    
    # Paso 2: Self-join para encontrar productos relacionados
    spark.sql("""
        CREATE OR REPLACE TEMP VIEW related_pairs AS
        SELECT 
            e1.product_id,
            e2.product_id AS other_product_id,
            e2.titulo AS other_titulo,
            e1.entity_text
        FROM exploded_entities e1
        JOIN exploded_entities e2 
            ON e1.entity_text = e2.entity_text
            AND e1.product_id != e2.product_id
    """)
    
    # Paso 3: Contar entidades compartidas y rankear
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW ranked_related AS
        SELECT 
            product_id,
            other_product_id,
            other_titulo,
            COUNT(entity_text) AS shared_count,
            ROW_NUMBER() OVER (
                PARTITION BY product_id 
                ORDER BY COUNT(entity_text) DESC
            ) AS rank
        FROM related_pairs
        GROUP BY product_id, other_product_id, other_titulo
    """)
    
    # Paso 4: Filtrar top N y agrupar en array
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW related_products_agg AS
        SELECT 
            product_id,
            COLLECT_LIST(
                STRUCT(other_titulo AS titulo, shared_count AS shared_entities_count)
            ) AS related_products
        FROM ranked_related
        WHERE rank <= {max_related}
        GROUP BY product_id
    """)
    
    # Paso 5: Join con datos originales
    query = """
    SELECT 
        d.*,
        COALESCE(r.related_products, ARRAY()) AS related_products
    FROM data_with_entities d
    LEFT JOIN related_products_agg r 
        ON d.titulo = r.product_id
    """
    df = spark.sql(query)
    df.createOrReplaceTempView("data_with_related")
    return df


def normalize_text_fields(spark):
    """
    Normaliza campos de texto: primera letra en mayúscula (initcap).
    Aplica a: titulo, descripcion, comentarios, caracteristicas
    """
    query = """
    SELECT 
        INITCAP(TRIM(titulo)) AS titulo,
        INITCAP(TRIM(descripcion)) AS descripcion,
        CASE 
            WHEN comentarios IS NOT NULL THEN
                TRANSFORM(comentarios, c -> 
                    STRUCT(
                        INITCAP(TRIM(c.usuario)) AS usuario,
                        INITCAP(TRIM(c.comentario)) AS comentario
                    )
                )
            ELSE comentarios
        END AS comentarios,
        CASE 
            WHEN caracteristicas IS NOT NULL THEN
                TRANSFORM(caracteristicas, carac -> INITCAP(TRIM(carac)))
            ELSE caracteristicas
        END AS caracteristicas,
        fecha,
        entities,
        entity_texts,
        related_products
    FROM data_with_related
    """
    df = spark.sql(query)
    df.createOrReplaceTempView("data_normalized_text")
    return df


def normalize_date_fields(spark):
    """
    Convierte fechas al formato DD/MM/YYYY.
    Maneja formato ISO (YYYY-MM-DD) del input.
    """
    query = """
    SELECT 
        titulo,
        descripcion,
        comentarios,
        caracteristicas,
        DATE_FORMAT(TO_DATE(fecha, 'yyyy-MM-dd'), 'dd/MM/yyyy') AS fecha,
        TRANSFORM(entities, e ->
            CASE 
                WHEN e.tipo = 'DATE' THEN
                    STRUCT(
                        DATE_FORMAT(TO_DATE(e.texto, 'yyyy-MM-dd'), 'dd/MM/yyyy') AS texto,
                        e.tipo AS tipo
                    )
                ELSE e
            END
        ) AS entities,
        entity_texts,
        related_products
    FROM data_normalized_text
    """
    df = spark.sql(query)
    df.createOrReplaceTempView("data_normalized_dates")
    return df


def generate_short_description(spark, max_length=140):
    """
    Genera descripcion_corta de máximo 140 caracteres usando Spark SQL.
    """
    query = f"""
    SELECT 
        *,
        CASE 
            WHEN LENGTH(descripcion) <= {max_length} THEN descripcion
            ELSE CONCAT(SUBSTRING(descripcion, 1, {max_length - 3}), '...')
        END AS descripcion_corta
    FROM data_normalized_dates
    """
    df = spark.sql(query)
    df.createOrReplaceTempView("data_final")
    return df


def normalize_data(spark):
    """
    Pipeline completo de normalización usando Spark SQL:
    1. Extraer entidades normalizadas
    2. Añadir productos relacionados
    3. Normalizar textos con mayúscula inicial
    4. Normalizar fechas a DD/MM/YYYY
    5. Generar descripción corta (140 chars)
    """
    # 1. Extraer entidades normalizadas
    extract_normalized_entities(spark)
    
    # 2. Añadir productos relacionados (máximo 10)
    get_related_products(spark, max_related=10)
    
    # 3. Normalizar textos
    normalize_text_fields(spark)
    
    # 4. Normalizar fechas
    normalize_date_fields(spark)
    
    # 5. Generar descripción corta
    df = generate_short_description(spark)
    
    return df


def save_to_mongodb(df, collection_name="documents"):
    """
    Guarda DataFrame en MongoDB Atlas.
    Requiere configuración de spark.mongodb.output.uri
    """
    df.write \
        .format("mongo") \
        .mode("append") \
        .option("collection", collection_name) \
        .save()


def save_processed_data(df, output_path):
    """Guarda DataFrame procesado en JSON"""
    df.write.mode("overwrite").json(output_path)


def main():
    """Función principal del CronJob"""
    spark = createSession()
    
    # Paths (ajustar según tu estructura)
    input_path = "/app/data/augmented/*.json"  # Carpeta augmented
    
    # Leer datos y registrar como tabla temporal
    read_augmented_data(spark, input_path)
    
    # Ejecutar pipeline de normalización (todo con Spark SQL)
    normalized_df = normalize_data(spark)
    
    # Guardar en MongoDB Atlas
    save_to_mongodb(normalized_df, collection_name="documents")
    
    # Opcional: guardar JSON local para debug
    # save_processed_data(normalized_df, "/app/data/processed")
    
    spark.stop()
    print("Normalización completada y datos guardados en MongoDB")


if __name__ == "__main__":
    main()
