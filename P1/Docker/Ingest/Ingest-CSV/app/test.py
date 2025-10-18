from unittest.mock import MagicMock, patch
import pytest
import os
import json
import time
import mariadb

from functions import *
# Pruebas
#Prueba 1: buscar_objeto retorna True/False 
def test_buscar_objeto():
    cursor = MagicMock()
    cursor.fetchone.return_value = (1,)
    assert buscar_objeto(cursor, "tabla", "key") is True

    cursor.fetchone.return_value = None
    assert buscar_objeto(cursor, "tabla", "key") is False


#Prueba 2: descargar el objeto
def test_descargar_objeto(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY", "fake_access")
    monkeypatch.setenv("AWS_SECRET_KEY", "fake_secret")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_BUCKET", "fake_bucket")
    monkeypatch.setenv("XPATH", "/tmp")
    monkeypatch.setattr("functions.AWS_ACCESS_KEY", "fake_access")
    monkeypatch.setattr("functions.AWS_SECRET_KEY", "fake_secret")
    monkeypatch.setattr("functions.AWS_REGION", "us-east-1")
    monkeypatch.setattr("functions.AWS_BUCKET", "fake_bucket")
    monkeypatch.setattr("functions.XPATH", "/tmp")

    with patch("functions.boto3.client") as mock_boto_client:
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        mock_s3.download_file.return_value = None

        key_name = "archivo_prueba.json"
        download_path = descargar_objeto(key_name)

        # Verificaciones
        path_correcto = os.path.join("/tmp", key_name)
        assert download_path == path_correcto
        mock_boto_client.assert_called_once_with(
            's3',
            aws_access_key_id="fake_access",
            aws_secret_access_key="fake_secret",
            region_name="us-east-1"
        )
        mock_s3.download_file.assert_called_once_with("fake_bucket", key_name, path_correcto)



#Prueba 3: Procesar objeto como json
def test_procesar_objeto_nbooks(tmp_path):
    file_path = tmp_path / "objeto1.json"

    # Datos de prueba
    prueba = [
        json.dumps({
            "title": "Libro A",
            "description": "Descripción del libro A",
            "authors": "Autor 1",
            "categories": "Ficción",
            "publisheddate": "2023-01-01",
            "publisher": "Editorial X",
            "previewlink": "http://previewA.com",
            "infolink": "http://infoA.com",
            "image": "http://imageA.com",
            "ratingscount": 4.5
        }),
        json.dumps({
            "title": "Libro B",
            "description": "Descripción del libro B",
            "authors": "Autor 2",
            "categories": "No Ficción",
            "publisheddate": "2023-01-01", 
            "publisher": "Editorial Y",
            "previewlink": "http://previewB.com",
            "infolink": "http://infoB.com",
            "image": "http://imageB.com",
            "ratingscount": 3.8
        }),
    ]

    #fingimos que el documento descargado tiene esos datos
    file_path.write_text("\n".join(prueba), encoding='utf-8')

    # Prueba
    documentos = procesar_objeto(str(file_path))

    assert len(documentos) == 2
    assert documentos[0] == {
        "title": "Libro A",
        "description": "Descripción del libro A",
        "authors": "Autor 1",
        "categories": "Ficción",
        "publisheddate": "2023-01-01",
        "publisher": "Editorial X",
        "previewlink": "http://previewA.com",
        "infolink": "http://infoA.com",
        "image": "http://imageA.com",
        "ratingscount": 4.5
    }
    assert documentos[1]["title"] == "Libro B"
    assert documentos[1]["ratingscount"] == 3.8
    assert documentos[1]["publisheddate"] == "2023-01-01"


# Prueba 4: probar todos los embeddings
def test_embedding_todos_documentos(monkeypatch):
    docs = [
        {"description": "uno"},
        {"description": ""},
        {"no_description": "x"},
    ]

    def fake_crear_embeddings_batch(textos, batch_size=64):
        embeddings = []
        for texto in textos:
            if texto == "uno":
                embeddings.append([1.029, 2.203, 3.029])
            else:
                embeddings.append(None)
        return embeddings

    monkeypatch.setattr("functions.crear_embeddings_batch", fake_crear_embeddings_batch)

    respuesta = embedding_todos_documentos(docs)
    assert respuesta[0]["embeddings"] == [1.029, 2.203, 3.029]
    assert respuesta[1]["embeddings"] is None
    assert respuesta[2]["embeddings"] is None


#Prueba 5: subir a elastic
@patch("functions.bulk") #evita importar bulk
def test_guardar_libros_elasticsearch(mock_bulk, monkeypatch):
    mock_es = MagicMock()
    monkeypatch.setattr("functions.conectar_elasticsearch", mock_es) #la conexion es un mock
    docs = [
        {"title": "T1", "description": "d1"},
        {"title": "T2", "description": "d2"}
    ]

    monkeypatch.setenv("ELASTIC_INDEX_BOOKS", "books")
    monkeypatch.setenv("ELASTIC_INDEX_NBOOKS", "nbooks")

    guardar_libros_elasticsearch(docs)
    # bulk llamado 
    assert mock_bulk.call_count >= 2


#Prueba 6: formatear fecha
def test_normalizar_fecha_varios_formatos():
    assert normalizar_fecha("2020-01-02") ==  datetime.strptime("2020-01-02", "%Y-%m-%d").date()
    assert normalizar_fecha("2020/01/02") ==  datetime.strptime("2020/01/02", "%Y/%m/%d").date()
    # Mes/año 
    respuesta = normalizar_fecha("2020-05")
    assert respuesta ==  datetime.strptime("2020-05-01", "%Y-%m-%d").date()
    # Año solo 
    respuesta2 = normalizar_fecha("1999")
    assert respuesta2 ==  datetime.strptime("1999-01-01", "%Y-%m-%d").date()
    # Formato inválido
    assert normalizar_fecha("no-fecha") is None

#Prueba 7: Formatear ratings
def test_normalizar_ratings():
    assert normalizar_ratings("4.5") == 4.5
    assert normalizar_ratings(10) == 10.0
    assert normalizar_ratings(None) is None
    # no numerico devuelve None
    assert normalizar_ratings("nulo") is None

#Prueba 8: Formatear "" extra
def test_limpiar_texto_varios_casos():
    assert limpiar_texto('  "hola"  ') == 'hola'
    assert limpiar_texto('""algo""') == 'algo'
    assert limpiar_texto(None) is None


#Prueba 9: insertar en authors
def test_insertar_author(monkeypatch):
    cursor = MagicMock()
    conn = MagicMock()
    monkeypatch.setenv("MARIADB_TABLE_AUTHORS", "authors")

    assert insertar_author(cursor, conn, "  ") is None

    cursor.fetchone.return_value = (42,) #reemplaza el id con 42 especificamente
    monkeypatch.setattr("functions.MARIADB_TABLE_AUTHORS", "authors")
    result = insertar_author(cursor, conn, "Gabriel García Márquez")
    assert result == 42 #verifica que devuelve el id
    cursor.execute.assert_any_call(
        "INSERT IGNORE INTO authors (name) VALUES (?)", ("Gabriel García Márquez",)
    )
    cursor.execute.assert_any_call(
        "SELECT id FROM authors WHERE name = ?", ("Gabriel García Márquez",)
    )

#Prueba 10: insertar en categories
def test_insertar_category(monkeypatch):
    cursor = MagicMock()
    conn = MagicMock()
    monkeypatch.setenv("MARIADB_TABLE_CATEGORIES", "categories")

    assert insertar_category(cursor, conn, None) is None

    cursor.fetchone.return_value = (41,)
    monkeypatch.setattr("functions.MARIADB_TABLE_CATEGORIES", "categories")
    result = insertar_category(cursor, conn, "Fantasy")
    assert result == 41
    cursor.execute.assert_any_call(
        "INSERT IGNORE INTO categories (name) VALUES (?)", ("Fantasy",)
    )
    cursor.execute.assert_any_call(
        "SELECT id FROM categories WHERE name = ?", ("Fantasy",)
    )

# Prueba 11: insertar books
def test_insertar_libro(monkeypatch):
    cursor = MagicMock()
    conn = MagicMock()
    monkeypatch.setenv("MARIADB_TABLE_BOOKS", "books")
    monkeypatch.setattr("functions.MARIADB_TABLE_BOOKS", "books")

    result = insertar_libro(conn, cursor, "obj123", title=None)
    assert result is None

    cursor.fetchone.return_value = [7]
    result = insertar_libro(
        conn,
        cursor,
        object_key="obj123",
        title="Cien años de soledad",
        description="Realismo mágico",
        published_date="1967-05-30",
        publisher="Sudamericana",
        preview_link="link1",
        info_link="link2",
        image_link="img",
        ratings_count=4.9
    )
    assert result == 7
    cursor.execute.assert_any_call("SELECT LAST_INSERT_ID()")
    conn.commit.assert_called()



# Prueba 12: relacionar authors y categories (corregido)
def test_relacionar_autores_categories(monkeypatch):
    cursor = MagicMock()
    conn = MagicMock()

    monkeypatch.setattr("functions.insertar_author", lambda c, conn, n: 41)
    monkeypatch.setattr("functions.insertar_category", lambda c, conn, n: 42)
    monkeypatch.setattr("functions.MARIADB_TABLE_AUTHORS_BOOKS", "authors_books")
    monkeypatch.setattr("functions.MARIADB_TABLE_CATEGORIES_BOOKS", "categories_books")

    relacionar_autores_categories(cursor, conn, book_id=7, authors="Cortázar", categories="Surrealismo")

    def normalize_sql(s):
        return "".join(s.split())  

    expected_statements = [
        ("INSERTIGNOREINTOauthors_books(book_id,author_id)VALUES(?,?)", (7, 41)),
        ("INSERTIGNOREINTOcategories_books(book_id,category_id)VALUES(?,?)", (7, 42))
    ]

    for expected_sql, expected_params in expected_statements:
        found = False
        for call in cursor.execute.call_args_list:
            sql, params = call[0]
            if normalize_sql(sql) == expected_sql and params == expected_params:
                found = True
                break
        assert found, f"No se encontró la llamada esperada: {expected_sql} con {expected_params}"

    conn.commit.assert_called_once()


# Prueba 13: insertar info
def test_insertar_info(monkeypatch):
    cursor = MagicMock()
    conn = MagicMock()
    key_name = "file1.json"

    monkeypatch.setattr("functions.insertar_libro", lambda *a, **k: 101)
    monkeypatch.setattr("functions.relacionar_autores_categories", lambda *a, **k: None)
    monkeypatch.setattr("functions.normalizar_fecha", lambda x: "2024-01-01")
    monkeypatch.setattr("functions.normalizar_ratings", lambda x: 4.5)
    monkeypatch.setattr("functions.limpiar_texto", lambda x: x)

    documentos = [
        {"title": "Libro 1", "authors": "Autor 1", "categories": "Drama"},
        {"title": "Libro 2", "authors": "Autor 2", "categories": "Ficción"},
    ]

    insertar_info(cursor, conn, key_name, documentos, cantidad=1)

    assert conn.commit.call_count >= 2
    conn.commit.assert_called()


# Prueba 14: insertar objeto como procesado
def test_insertar_object(monkeypatch):
    cursor = MagicMock()
    conn = MagicMock()
    monkeypatch.setenv("MARIADB_TABLE", "objects")
    monkeypatch.setattr("functions.MARIADB_TABLE", "objects")

    documentos = [{"a": 1}, {"b": 2}, {"c": 3}]
    key_name = "objeto1.json"

    insertar_object(cursor, conn, key_name, documentos, procesado=True)

    executed_sql = "".join(cursor.execute.call_args[0][0].split())
    expected_sql = "INSERTINTOobjects(key_name,num_documents,procesado)VALUES(?,?,?)"

    assert executed_sql == expected_sql
    assert cursor.execute.call_args[0][1] == (key_name, 3, True)
    conn.commit.assert_called_once()


#-------------------------------------------
if __name__ == "__main__":
    pytest.main([__file__, "-v"])