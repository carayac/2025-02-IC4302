import requests
import os
import sys
import logging

logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

#Variables
headers = {"User-Agent": "Mozilla/5.0"}  #para evitar ser detectado como bot
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
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        html_content = response.content
        return html_content

    else:
        logger.error(f"Request failed: {response.status_code}")
        return None
    


def descargarHtml(html, category, num):
    file_path = os.path.join(folder, f"{category}_{num:03d}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Guardado: {file_path}")


