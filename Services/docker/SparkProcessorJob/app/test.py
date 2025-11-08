import os
import sys

import pytest
from pyspark.sql import Row, SparkSession
from pyspark.sql.types import (ArrayType, IntegerType, StringType, StructField,
                               StructType)

APP_DIR = os.path.dirname(os.path.dirname(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from functions import (  # noqa: E402
    add_related_products,
    format_dates_ddmmyyyy_sql,
    normalize_entities,
    summary,
    uppercase_first_letter,
)


@pytest.fixture(scope="session")
def spark():
    spark_session = (
        SparkSession.builder.master("local[1]")
        .appName("spark-processor-tests")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    yield spark_session
    spark_session.stop()


def test_uppercase_first_letter_capitalizes_string_columns(spark):
    data = [
        ("producto uno", "descripcion uno", 5),
        ("OTRO PRODUCTO", None, 10),
    ]
    schema = StructType(
        [
            StructField("titulo", StringType(), True),
            StructField("descripcion", StringType(), True),
            StructField("calificacion", IntegerType(), True),
        ]
    )
    df = spark.createDataFrame(data, schema)

    result = uppercase_first_letter(df).collect()

    assert result[0].titulo == "Producto Uno"
    assert result[0].descripcion == "Descripcion Uno"
    assert result[0].calificacion == 5
    assert result[1].titulo == "Otro Producto"
    assert result[1].descripcion is None
    assert result[1].calificacion == 10


def test_normalize_entities_handles_nested_structures(spark):
    schema = StructType(
        [
            StructField("titulo", StringType(), True),
            StructField(
                "entities",
                ArrayType(
                    StructType(
                        [
                            StructField("texto", StringType(), True),
                            StructField("tipo", StringType(), True),
                            StructField("score", IntegerType(), True),
                        ]
                    )
                ),
                True,
            ),
            StructField(
                "comentarios",
                StructType(
                    [
                        StructField("usuario", StringType(), True),
                        StructField("mensaje", StringType(), True),
                        StructField("likes", IntegerType(), True),
                    ]
                ),
                True,
            ),
            StructField("tags", ArrayType(StringType()), True),
        ]
    )

    data = [
        (
            "producto demo",
            [
                {"texto": "marca x", "tipo": "brand", "score": 1},
                {"texto": "modelo y", "tipo": "type", "score": 2},
            ],
            {"usuario": "ana lopez", "mensaje": "muy bueno", "likes": 15},
            ["cafe premium", "grano oscuro"],
        )
    ]

    df = spark.createDataFrame(data, schema)

    result = normalize_entities(df).collect()[0]

    assert [entity.texto for entity in result.entities] == ["Marca X", "Modelo Y"]
    assert [entity.tipo for entity in result.entities] == ["Brand", "Type"]
    assert [entity.score for entity in result.entities] == [1, 2]
    assert result.comentarios.usuario == "Ana Lopez"
    assert result.comentarios.mensaje == "Muy Bueno"
    assert result.comentarios.likes == 15
    assert result.tags == ["Cafe Premium", "Grano Oscuro"]


def test_format_dates_ddmmyyyy_sql_formats_dates(spark):
    df = spark.createDataFrame(
        [
            Row(date_extracted="2024/01/15"),
            Row(date_extracted="2024-02-20"),
            Row(date_extracted=None),
        ]
    )

    result = format_dates_ddmmyyyy_sql(df).collect()

    assert [row.date_extracted for row in result] == ["15/01/2024", "20/02/2024", None]


def test_summary_generates_short_description(spark):
    df = spark.createDataFrame(
        [
            Row(description="texto corto"),
            Row(description=" ".join(["palabra" for _ in range(100)])),
            Row(description=None),
        ]
    )

    result = summary(df).collect()

    assert result[0]["short-description"] == "texto corto"
    assert result[1]["short-description"].endswith("...")
    assert len(result[1]["short-description"]) <= 143
    assert result[2]["short-description"] == ""


def test_add_related_products_builds_related_list(spark):
    schema = StructType(
        [
            StructField("titulo", StringType(), True),
            StructField("description", StringType(), True),
            StructField(
                "entities",
                ArrayType(
                    StructType(
                        [
                            StructField("texto", StringType(), True),
                            StructField("tipo", StringType(), True),
                        ]
                    )
                ),
                True,
            ),
        ]
    )

    df = spark.createDataFrame(
        [
            (
                "Producto Cafe",
                "Descripcion A",
                [{"texto": "cafe arabica", "tipo": "ingrediente"}],
            ),
            (
                "Producto Cafe Premium",
                "Descripcion B",
                [{"texto": "cafe arabica", "tipo": "ingrediente"}],
            ),
            (
                "Producto Te",
                "Descripcion C",
                [{"texto": "te negro", "tipo": "ingrediente"}],
            ),
        ],
        schema,
    )

    result = add_related_products(df, max_relacionados=2)
    rows = {row.titulo: row for row in result.collect()}

    relacionados_cafe = [rel.titulo for rel in rows["Producto Cafe"].productos_relacionados]
    relacionados_te = rows["Producto Te"].productos_relacionados

    assert "Producto Cafe Premium" in relacionados_cafe
    assert "Producto Cafe" not in relacionados_cafe
    assert relacionados_te == []
