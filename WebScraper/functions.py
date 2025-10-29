from venv import logger
import requests
import os
import re

#Variables
url = "https://app.edutin.com/academy/"
folder = "productos"
os.makedirs(folder, exist_ok=True)

categorias = {
    "programacion": "67",
    "cocina": "71",
    "marketing": "77",
    "deporte": "78",
    "psicologia": "80",
    "ciencias": "82",
}



def obtenerProducto(url):
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.content
        return html_content

    else:
        logger(f"Request failed: {response.status_code}")
        return None
    


