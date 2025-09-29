from flask import request,jsonify
import requests
import logging
import sys
import os


logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

#Evironmental variable for embedding
ENDPOINT = os.getenv("EMBEDDINGENDPOINT")

def get_embedding(text):
    try:
        #adding params to the json data
        data={"text":text}
        response = requests.post(ENDPOINT,json=data)
        #get the json version
        post_response=response.json()
        return post_response
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en la petición al endpoint {ENDPOINT}: {e}")
        raise 
    except Exception as e:
        logger.error(f"Error inesperado generando embedding: {e}")
        raise 
