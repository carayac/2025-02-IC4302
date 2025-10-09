import json
import pytest
import numpy as np  
from unittest.mock import patch
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

#Verificamos que el endpoint status funcione correctamente
@patch('app.model.encode', return_value=np.array([0.1, 0.2, 0.3]))  
def test_status_endpoint(mock_encode, client):
    response = client.get('/status')
    assert response.status_code == 200

    data = response.get_json()
    assert 'text' in data
    assert 'embedding' in data
    assert isinstance(data['embedding'], list)
    assert data['embedding'] == [0.1, 0.2, 0.3]
    assert data['text'] == "Si funciona"

#Verificamos que el endpoint encode funcione correctamente
@patch('app.model.encode', return_value=np.array([0.5, 0.6, 0.7]))  
def test_encode_valid(mock_encode, client):
    payload = {'text': 'Hola'}
    response = client.post(
        '/encode',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['text'] == 'Hola'
    assert data['embedding'] == [0.5, 0.6, 0.7]
    mock_encode.assert_called_once_with('Hola')

#Verificamos que el endpoint encode maneje correctamente la falta del campo 'text'
def test_encode_missing_field(client):
    payload = {'mensaje': 'falta text'}
    response = client.post(
        '/encode',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data['Error'] == 'Falta el campo text'