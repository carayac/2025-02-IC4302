from flask import Flask, jsonify
import requests
from os import getenv
import sys
import os, json
from pymemcache.client.base import Client

VESPA_ENDPOINT = getenv("VESPA_ENDPOINT", "http://localhost:8081")
VESPA_COLLECTION = getenv("VESPA_COLLECTION", "animales")

app = Flask(__name__)

#Variables para memcached
MEMCACHED_HOST = os.getenv("MEMCACHED_HOST", "localhost")
MEMCACHED_PORT = int(os.getenv("MEMCACHED_PORT", "11211"))
CACHE_TTL_SECONDS = 60

memcached = Client(("databases-memcached", 11211))


def cache_get(key):
    try:
        raw = memcached.get(key)
        if not raw:
            return None
        
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None

def cache_set(key: str, value: dict, ttl: int = CACHE_TTL_SECONDS):
    try:
        memcached.set(key, json.dumps(value), expire=ttl)
    except Exception:
        pass


def get_vespa_docs():
    try:
        query = {
            "yql": "select name, color from animales where true",
            "hits": 100,
            "timeout": "10s"
        }
            
        response = requests.post(f"{VESPA_ENDPOINT}/search/", json=query, timeout=10)
        if response.status_code == 200:
                data = response.json()
                total_count = data.get('root', {}).get('fields', {}).get('totalCount', 0)
                children_count = len(data.get('root', {}).get('children', []))
                        
                docs = []
                for hit in data.get("root", {}).get("children", []):
                    fields = hit.get("fields", {})
                    docs.append({
                        "name": fields.get("name", "Desconocido"),
                        "color": fields.get("color", "N/A")
                    })
                return docs
        else:
                print(f"Query falló: {response.status_code} - {response.text[:200]}")
                return []
        
    except Exception as e:
        print(f"Error en get_vespa_docs: {e}")
        return []

@app.route("/animales", methods=["GET"])
def get_animales():

    cache_key = "animales-nombre"

    #Busca en caché
    cached = cache_get(cache_key)
    if cached is not None:
            return jsonify({"source": "cache", "data": cached}) #Caché Hit

    #En caso de caché miss, abre conexion con bd y consulta
    docs = get_vespa_docs()    
    animales = [{"nombre": doc.get("name", "N/A")} for doc in docs]

    #Guarda en la caché despues de haber consultado BD
    cache_set(cache_key, animales, CACHE_TTL_SECONDS)
    return jsonify({"source": "db", "data": animales})

@app.route("/colores", methods=["GET"])
def get_colores():

    cache_key = "animales-colores"

    #Busca en caché
    cached = cache_get(cache_key)
    if cached is not None:
            return jsonify({"source": "cache", "data": cached}) #Caché Hit

    #En caso de caché miss, abre conexion con bd y consulta
    docs = get_vespa_docs()
    print(f"Documentos recibidos: {len(docs)}")
    
    colores_dict = {}
    for doc in docs:
        color = doc.get("color", "N/A")
        nombre = doc.get("name", "N/A")
        if color not in colores_dict:
            colores_dict[color] = []
        colores_dict[color].append(nombre)
    
    colores_list = []
    for color, animales_list in colores_dict.items():
        colores_list.append({
            "color": color,
            "animals": ", ".join(animales_list)
        })
    
    #Guarda en la caché despues de haber consultado BD
    cache_set(cache_key, colores_list, CACHE_TTL_SECONDS)
    return jsonify({"source": "db", "data": colores_list})   # Devolver la lista de colores con sus animales

if __name__ == "__main__":
    app.run(host='localhost', port=5000, debug=True)