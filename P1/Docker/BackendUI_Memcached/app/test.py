from unittest.mock import MagicMock
import types
import sys
import os
import importlib.util
import pytest


def import_app(monkeypatch):
    # create dummy
    dummy_auth_bp = object()
    dummy_friend_bp = object()
    dummy_prompt_bp = object()
    dummy_user_bp = object()

    # create dummy modules
    auth_mod = types.SimpleNamespace(auth_blueprint=dummy_auth_bp)
    friend_mod = types.SimpleNamespace(friend_blueprint=dummy_friend_bp)
    prompt_mod = types.SimpleNamespace(prompt_blueprint=dummy_prompt_bp)
    user_mod = types.SimpleNamespace(user_blueprint=dummy_user_bp)

    # register dummy modules in sys.modules before import
    monkeypatch.setitem(sys.modules, "routes.authentication", auth_mod)
    monkeypatch.setitem(sys.modules, "routes.friend", friend_mod)
    monkeypatch.setitem(sys.modules, "routes.prompt", prompt_mod)
    monkeypatch.setitem(sys.modules, "routes.user", user_mod)

    from flask import Flask
    register_mock = MagicMock()
    monkeypatch.setattr(Flask, "register_blueprint", register_mock, raising=False)

    # Load the application module
    module_dir = os.path.dirname(__file__)
    module_path = os.path.join(module_dir, "app.py")
    spec = importlib.util.spec_from_file_location("tested_app", module_path)
    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module, register_mock, dummy_auth_bp, dummy_friend_bp, dummy_prompt_bp, dummy_user_bp


def test_blueprints_registered(monkeypatch):
    """
    Verifica que la aplicacion registre todos los blueprints
    """
    module, register_mock, dummy_auth_bp, dummy_friend_bp, dummy_prompt_bp, dummy_user_bp = import_app(monkeypatch)

    # There should be exactly 4 calls to register_blueprint
    assert register_mock.call_count == 4, f"Expected 4 blueprint registrations, got {register_mock.call_count}"


    registered_blueprints = [call.args[0] for call in register_mock.call_args_list]

    assert dummy_auth_bp in registered_blueprints, "Auth blueprint was not registered"
    assert dummy_friend_bp in registered_blueprints, "Friend blueprint was not registered"
    assert dummy_prompt_bp in registered_blueprints, "Prompt blueprint was not registered"
    assert dummy_user_bp in registered_blueprints, "User blueprint was not registered"


def test_health_endpoint(monkeypatch):
    """
    Verifica que el endpoint /healt de la respuesta esperada de 200
    """
    module, register_mock, *_ = import_app(monkeypatch)
    app = module.app
    client = app.test_client()

    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"status": "ok"}, f"Respuesta inesperada: {data}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


