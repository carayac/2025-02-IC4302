def import_app(monkeypatch):
    """
    Carga el módulo app.py reemplazando dependencias externas
    (routes.*) por objetos simulados para evitar importaciones reales.
    """
    # Create dummies
    dummy_auth_bp = object()
    dummy_friend_bp = object()
    dummy_prompt_bp = object()
    dummy_user_bp = object()

    # Create modules
    auth_mod = types.SimpleNamespace(auth_blueprint=dummy_auth_bp)
    friend_mod = types.SimpleNamespace(friend_blueprint=dummy_friend_bp)
    prompt_mod = types.SimpleNamespace(prompt_blueprint=dummy_prompt_bp)
    user_mod = types.SimpleNamespace(user_blueprint=dummy_user_bp)

    #sys.modules
    monkeypatch.setitem(sys.modules, "routes.authentication", auth_mod)
    monkeypatch.setitem(sys.modules, "routes.friend", friend_mod)
    monkeypatch.setitem(sys.modules, "routes.prompt", prompt_mod)
    monkeypatch.setitem(sys.modules, "routes.user", user_mod)
  
    from flask import Flask
    register_mock = MagicMock()
    monkeypatch.setattr(Flask, "register_blueprint", register_mock, raising=False)

    #load modules
    module_dir = os.path.dirname(__file__)
    module_path = os.path.join(module_dir, "app.py")
    spec = importlib.util.spec_from_file_location("tested_app", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module, register_mock, dummy_auth_bp, dummy_friend_bp, dummy_prompt_bp, dummy_user_bp


def test_blueprints_registered(monkeypatch):
    """
    Verifica que se registren correctamente los 4 blueprints con sus prefijos.
    """
    module, register_mock, dummy_auth_bp, dummy_friend_bp, dummy_prompt_bp, dummy_user_bp = import_app(monkeypatch)

    assert register_mock.call_count == 4, f"Se esperaban 4 blueprints, pero se registraron {register_mock.call_count}"

    # Extraer argumentos
    registered_blueprints = [call.args[0] for call in register_mock.call_args_list]
    prefixes = [call.kwargs.get("url_prefix") for call in register_mock.call_args_list]

    # Validar presencia de blueprints
    assert dummy_auth_bp in registered_blueprints, "Blueprint de auth no registrado"
    assert dummy_friend_bp in registered_blueprints, "Blueprint de friend no registrado"
    assert dummy_prompt_bp in registered_blueprints, "Blueprint de prompt no registrado"
    assert dummy_user_bp in registered_blueprints, "Blueprint de user no registrado"

    # Validar prefijos
    expected_prefixes = ["/promptsy/auth", "/promptsy/friend", "/promptsy/prompt", "/promptsy/user"]
    for prefix in expected_prefixes:
        assert prefix in prefixes, f"Falta prefijo {prefix}"


def test_health_endpoint(monkeypatch):
    """
    Verifica que el endpoint /health devuelva un JSON con status 'ok' y código 200.
    """
    module, _, *_ = import_app(monkeypatch)
    app = module.app
    client = app.test_client()

    response = client.get("/health")
    assert response.status_code == 200, f"Esperado 200, recibido {response.status_code}"
    data = response.get_json()
    assert data == {"status": "ok"}, f"Respuesta inesperada: {data}"
