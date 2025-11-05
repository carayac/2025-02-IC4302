import sys
import types
import pytest

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, size

import functions

# Provide minimal stubs for modules that functions.py imports at import-time
app_mod = types.ModuleType("app")
env_mod = types.ModuleType("app.env")
env_mod.URI_MONGODB = "mongodb://localhost:27017/test"
env_mod.VOLUMEN_PVC = "/tmp"
sys.modules["app"] = app_mod
sys.modules["app.env"] = env_mod

# Stub sklearn.feature_extraction.text.TfidfVectorizer used in functions.py so import succeeds
sk_mod = types.ModuleType("sklearn")
fe_mod = types.ModuleType("sklearn.feature_extraction")
text_mod = types.ModuleType("sklearn.feature_extraction.text")

class _DummyMatrix:
    def __init__(self, n):
        self._n = n
    def sum(self, axis):
        class A:
            def __init__(self, n):
                # produce deterministic scores
                self.A1 = list(range(n))
        return A(self._n)

class _DummyVectorizer:
    def __init__(self, *args, **kwargs):
        pass
    def fit_transform(self, sentences):
        return _DummyMatrix(len(sentences))

text_mod.TfidfVectorizer = _DummyVectorizer
sys.modules["sklearn"] = sk_mod
sys.modules["sklearn.feature_extraction"] = fe_mod
sys.modules["sklearn.feature_extraction.text"] = text_mod




@pytest.fixture(scope="session")
def spark():
    spark = SparkSession.builder.master("local[1]").appName("pytest-spark").getOrCreate()
    yield spark
    spark.stop()


def test_uppercase_first_letter(spark):
    data = [{"titulo": "curso de ventas", "descripcion": "aprende a vender"}]
    df = spark.createDataFrame(data)
    df2 = functions.uppercase_first_letter(df)
    row = df2.collect()[0]
    assert row["titulo"] == "Curso De Ventas"
    assert row["descripcion"] == "Aprende A Vender"


def test_format_dates_ddmmyyyy_sql(spark):
    data = [{"fecha": "2025-10-25"}, {"fecha": "2025/10/25"}]
    df = spark.createDataFrame(data)
    df2 = functions.format_dates_ddmmyyyy_sql(df)
    vals = [r["fecha"] for r in df2.collect()]
    assert vals == ["25/10/2025", "25/10/2025"]


def test_normalize_entities(spark):
    data = [{
        "titulo": "curso",
        "entities": [{"texto": "servicios financieros", "tipo": "Product"}],
        "comentarios": [{"comentario": "muy util", "usuario": "u1"}]
    }]
    df = spark.createDataFrame(data)
    df2 = functions.normalize_entities(df)
    r = df2.collect()[0]
    # entities is an array of structs
    ent = r["entities"][0]
    assert ent["texto"] == "Servicios Financieros"
    # comentarios normalized as well
    com = r["comentarios"][0]
    assert com["comentario"] == "Muy Util"


def test_add_related_products_basic(spark):
    data = [
        {"titulo": "A", "descripcion": "descA", "entities": [{"texto": "X", "tipo": "Product"}]},
        {"titulo": "B", "descripcion": "descB", "entities": [{"texto": "X", "tipo": "Product"}]}
    ]
    df = spark.createDataFrame(data)
    df2 = functions.add_related_products(df, max_relacionados=10)
    rows = df2.collect()
    # each product should have one related product (the other)
    mapping = {r["titulo"]: r["productos_relacionados"] for r in rows}
    assert mapping["A"] is not None and len(mapping["A"]) == 1
    assert mapping["A"][0]["titulo"] == "B"
    assert mapping["B"] is not None and len(mapping["B"]) == 1
    assert mapping["B"][0]["titulo"] == "A"


def test_full_pipeline_write_local(spark, tmp_path):
    # Prepare a small input JSON file (multiline JSON allowed)
    sample = {
        "titulo": "Curso De Ventas De Servicios Financieros",
        "descripcion": "Desarrolla habilidades para vender servicios financieros.",
        "entities": [
            {"texto": "Servicios Financieros", "tipo": "Product"},
            {"texto": "2025-10-25", "tipo": "Date"}
        ],
        "fecha": "2025-10-25",
        "caracteristicas": ["Modalidad 100% Virtual"],
        "comentarios": [{"comentario": "muy util", "usuario": "est1"}]
    }

    in_dir = tmp_path / "input"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()

    # Write a single JSON file
    import json
    p = in_dir / "e1.json"
    p.write_text(json.dumps(sample, ensure_ascii=False))

    # Read, normalize and save locally (no Mongo)
    functions.read_augmented_data(spark, str(in_dir))
    df = functions.normalize_data(spark)
    # Save locally
    functions.save_processed_data(df, str(out_dir))

    # Assert that output files were written
    files = list(out_dir.iterdir())
    assert len(files) > 0
