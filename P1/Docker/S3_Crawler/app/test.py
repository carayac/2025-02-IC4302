import sys
import os
import types
import pytest
from unittest.mock import MagicMock, patch


def import_crawler(monkeypatch):
    fake_boto3 = MagicMock()
    fake_pika = MagicMock()
    fake_prometheus = types.SimpleNamespace(
        Counter=MagicMock(return_value=MagicMock()),
        Histogram=MagicMock(return_value=MagicMock()),
        start_http_server=MagicMock(),
        generate_latest=MagicMock(return_value=b"metrics"),
        CONTENT_TYPE_LATEST="text/plain"
    )

    fake_logging = MagicMock()
    fake_time = MagicMock()
    fake_time.time.side_effect = [0, 10]  # simulamos 10 segundos de duración

    #mocks
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setitem(sys.modules, "pika", fake_pika)
    monkeypatch.setitem(sys.modules, "prometheus_client", fake_prometheus)
    monkeypatch.setitem(sys.modules, "logging", fake_logging)
    monkeypatch.setitem(sys.modules, "time", fake_time)

    #enviroment
    monkeypatch.setenv("S3_BUCKET", "fake-bucket")
    monkeypatch.setenv("S3_PREFIXES", "folder1,folder2")
    monkeypatch.setenv("AWS_ACCESS_KEY", "key")
    monkeypatch.setenv("AWS_SECRET_KEY", "secret")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("RABBITMQ", "localhost")
    monkeypatch.setenv("RABBITMQ_QUEUE_CSV", "csv")
    monkeypatch.setenv("RABBITMQ_QUEUE_PARKET", "parquet")
    monkeypatch.setenv("RABBITMQ_USER", "user")
    monkeypatch.setenv("RABBITMQ_PASS", "pass")

    #from module
    module_dir = os.path.dirname(__file__)
    module_path = os.path.join(module_dir, "app.py")

    import importlib.util
    spec = importlib.util.spec_from_file_location("tested_crawler", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module, fake_boto3, fake_pika, fake_prometheus, fake_logging, fake_time



def test_import_initializes_metrics_and_server(monkeypatch):
    """Verifies metrics"""
    module, fake_boto3, fake_pika, fake_prometheus, fake_logging, fake_time = import_crawler(monkeypatch)

    fake_prometheus.Counter.assert_called_once()
    fake_prometheus.Histogram.assert_called_once()
    fake_prometheus.start_http_server.assert_called_once_with(8000)
    fake_logging.basicConfig.assert_called_once()


def test_rabbitmq_connection_success(monkeypatch):
    """Verifies rabbitmq"""
    module, fake_boto3, fake_pika, fake_prometheus, fake_logging, fake_time = import_crawler(monkeypatch)

    fake_conn = MagicMock()
    fake_channel = MagicMock()
    fake_conn.channel.return_value = fake_channel
    fake_pika.BlockingConnection.return_value = fake_conn

    conn, channel = module.rabbitmq_connection()

    fake_pika.PlainCredentials.assert_called_once_with("user", "pass")
    fake_pika.ConnectionParameters.assert_called_once()
    fake_channel.queue_declare.assert_any_call(queue="csv", durable=False)
    fake_channel.queue_declare.assert_any_call(queue="parquet", durable=False)
    fake_logging.info.assert_any_call("Succesfully connected and created queues")

    assert conn == fake_conn
    assert channel == fake_channel


def test_rabbitmq_connection_failure(monkeypatch):
    """Verifies errors on rabbitmq"""
    module, fake_boto3, fake_pika, fake_prometheus, fake_logging, fake_time = import_crawler(monkeypatch)
    fake_pika.BlockingConnection.side_effect = Exception(" RabbitMQ failed ")

    with pytest.raises(Exception):
        module.rabbitmq_connection()

    fake_logging.error.assert_called()
    assert "RabbitMQ" in fake_logging.error.call_args[0][0]


def test_publish_message_success(monkeypatch):
    """verifies publish messages"""
    module, *_ = import_crawler(monkeypatch)
    fake_channel = MagicMock()

    module.publish_message(fake_channel, "csv", "archivo1.json")

    fake_channel.basic_publish.assert_called_once()
    assert "archivo1.json" in str(fake_channel.basic_publish.call_args)
    assert "csv" in str(fake_channel.basic_publish.call_args)


def test_publish_message_failure(monkeypatch):
    """Verifies errors publishinf messages."""
    module, fake_boto3, fake_pika, fake_prometheus, fake_logging, fake_time = import_crawler(monkeypatch)
    fake_channel = MagicMock()
    fake_channel.basic_publish.side_effect = Exception("Fail publishing on RabbitMQ")

    module.publish_message(fake_channel, "csv", "archivo.json")
    fake_logging.error.assert_called()
    assert "Error publicando" in fake_logging.error.call_args[0][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
