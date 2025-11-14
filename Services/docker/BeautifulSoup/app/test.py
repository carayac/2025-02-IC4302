import os
import json
from unittest.mock import MagicMock, mock_open, patch
from bs4 import BeautifulSoup
import pytest

import app


#Test 1. parse author

def test_parse_author(monkeypatch):
    html = BeautifulSoup(
        "<div>Información del autor Juan Pérez profesor de ciencias aplicadas</div>",
        "lxml"
    )

    name, comment = app.parse_author(html)

    assert name == "Juan Pérez"
    assert "profesor" in comment.lower()


#Test 2.extract_course_data con json-ld

def test_extract_course_data_json_ld():
    html = """
    <html><body>
    <script type="application/ld+json">
    {
        "name": "Curso de Excel",
        "description": "<p>Aprende Excel desde cero</p>",
        "image": "img.jpg",
        "aggregateRating": {"ratingValue": "4.8"},
        "review": [
            {
                "author": {"name": "Ana"},
                "description": "Muy bueno",
                "reviewRating": {"ratingValue": "5"},
                "datePublished": "2023-01-10"
            }
        ]
    }
    </script>
    </body></html>
    """

    data = app.extract_course_data(html, "file.html")

    assert data["title"] == "Curso de Excel"
    assert data["description"] == "Aprende Excel desde cero"
    assert data["image"] == "img.jpg"
    assert data["rating_value"] == 4.8

    assert len(data["reviews"]) == 1
    assert data["reviews"][0]["user"] == "Ana"
    assert data["reviews"][0]["comment"] == "Muy bueno"
    assert data["reviews"][0]["rating"] == 5.0
    assert data["reviews"][0]["date"] == "10/01/2023"


#Test 3. fallbacks de extract course
def test_extract_course_data_fallbacks():
    html = """
    <html>
        <head>
            <title>Mi Curso</title>
            <meta name="description" content="Descripción breve del curso" />
            <meta property="og:image" content="og.jpg" />
        </head>
        <body>
            <p>Contenido del curso</p>
        </body>
    </html>
    """

    data = app.extract_course_data(html, "file.html")

    assert data["title"] == "Mi Curso"
    assert data["description"] == "Descripción breve del curso"
    assert data["image"] == "og.jpg"


#Test 4. download_html_from_s3
def test_download_html_from_s3(monkeypatch):
    class FakeBody:
        def read(self):
            return b"<html>OK</html>"

    class FakeS3:
        def get_object(self, Bucket, Key):
            assert Bucket == app.S3_BUCKET
            return {"Body": FakeBody()}

    monkeypatch.setattr(app, "s3", FakeS3())

    html = app.download_html_from_s3("folder/file.html")
    assert html == "<html>OK</html>"


# Test 5. process_message 

def test_process_message(monkeypatch, tmp_path):

    # fake mongo_collection
    fake_coll = MagicMock()
    monkeypatch.setattr(app, "mongo_collection", lambda: fake_coll)

    monkeypatch.setattr(app, "download_html_from_s3", lambda x: "<html>DATA</html>")

    fake_data = {"title": "Test", "author": {"name": "A"}}
    monkeypatch.setattr(app, "extract_course_data", lambda html, fn: fake_data)

    monkeypatch.setattr(app, "SHARED_VOLUME_PATH", str(tmp_path))

    ch = MagicMock()

    monkeypatch.setattr(app, "RABBITMQ_QUEUE_ENTITY", "entity-queue")
 
    m = mock_open()
    with patch("builtins.open", m):

        body = json.dumps({"id": "folder/test.html"}).encode()

        method = MagicMock()
        method.delivery_tag = 999

        app.process_message(ch, method, None, body)

    fake_coll.update_one.assert_any_call(
        {"_id": "folder/test.html"},
        {"$set": {"processing": "started"}},
        upsert=True
    )

    fake_coll.update_one.assert_any_call(
        {"_id": "folder/test.html"},
        {"$set": {"processing": "completed"}}
    )

    ch.basic_publish.assert_called_once()
    args, kwargs = ch.basic_publish.call_args

    assert kwargs["routing_key"] == "entity-queue"
    sent = json.loads(kwargs["body"])
    assert sent["_id"] == "folder/test.html"
    assert "jsonPath" in sent
    
    ch.basic_ack.assert_called_once_with(delivery_tag=999)
