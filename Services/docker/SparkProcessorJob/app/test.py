import sys
import types
import pytest
from pyspark.sql import SparkSession
import functions

# Minimal stubs so tests can import project code without external env
app_mod = types.ModuleType("app")
env_mod = types.ModuleType("app.env")
env_mod.URI_MONGODB = "mongodb://localhost:27017/test"
env_mod.VOLUMEN_PVC = "/tmp"
sys.modules["app"] = app_mod
sys.modules["app.env"] = env_mod

# Simple sklearn stub used by functions.py
sk_mod = types.ModuleType("sklearn")
fe_mod = types.ModuleType("sklearn.feature_extraction")
text_mod = types.ModuleType("sklearn.feature_extraction.text")

class _DummyMatrix:
    def __init__(self, n):
        self._n = n
    def sum(self, axis):
        class A:
            def __init__(self, n):
                self.A1 = [1] * n
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
    vals = sorted([r["fecha"] for r in df2.collect()])
    assert vals == ["25/10/2025", "25/10/2025"]


def test_normalize_entities_capitalizes_nested(spark):
    data = [{
        "titulo": "curso",
        "entities": [{"texto": "servicios financieros", "tipo": "Product"}],
    }]
    df = spark.createDataFrame(data)
    df2 = functions.normalize_entities(df)
    r = df2.collect()[0]
    ent = r["entities"][0]
    assert ent["texto"] == "Servicios Financieros"


def test_add_related_products_callable():
    # Ensure the function exists and is callable. Detailed behavior is tested elsewhere
    assert hasattr(functions, "add_related_products")
    assert callable(functions.add_related_products)
