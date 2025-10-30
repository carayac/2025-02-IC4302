import requests
import os
import sys
import logging
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import subprocess 


logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

#credenciales
os.environ["AWS_ACCESS_KEY_ID"] = "AKIAQ2VOGXQD2ICLMJXL"
os.environ["AWS_SECRET_ACCESS_KEY"] = "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"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


#Variables
headers = {"User-Agent": "Mozilla/5.0"}  #para evitar ser detectado como bot
urlBase = "https://app.edutin.com/search/courses?q="
categories = ["programacion", "cocina", "creativo", "salud", "negocio", "deporte", "psicologia", "ciencia", "cloud computing", "mantenimiento", "moda", "arte", "idiomas", "marketing"]
folder = "productos"
scroll_pause_time = 15
cursoId = 1
carpeta_grupo = "CARPETA_HCDCP"



#obtiene html base
def obtenerBusqueda(url):
    driver = webdriver.Chrome()
    driver.get(url)
    driver.implicitly_wait(5)

    #en la pagina hay que hacer scroll para que se carguen los cursos 
    last_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(50):
        # Scroll down
        scrollable_div = driver.find_element(By.ID, "main-scroll")
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
        # Esperar a que cargue
        time.sleep(scroll_pause_time)
        # Comparar si ya llegamos al final
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    html = driver.page_source
    driver.quit() 
    return html

#hace request en la url y obtiene html
def obtenerProductos(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            logger.error(f"Request failed: {response.status_code} para link: {url}")
            return None
    except Exception as e:
        logger.error(f"Error obteniendo {url}: {e}")
        return None


#obtiene los links para scrapear todos los links de los cursos a partir de html base
def obtenerLinks(htmlBase):
    if not htmlBase:
        return []
    # Busca todos los href que empiecen con https://edutin.com/
    links = re.findall(r'href="(https://edutin\.com/[^"]+)"', htmlBase)

    cursos = [l for l in links 
              if "curso-de-" in l and not any(ext in l for ext in [".jpg", ".png", ".svg", "facebook", "twitter"])]
    return list(set(cursos))[:500]  # eliminar duplicados y solo los primeros 500


#guarda en archivo
def descargarHtml(html, num):
    if not html:
        logger.warning(f"HTML vacío para el curso #{num}")
        return
    folder_path = os.path.join(folder)
    os.makedirs(folder_path, exist_ok=True)

    file_path = os.path.join(folder_path, f"curso_{num:03d}.html")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"Guardado: {file_path}")
    except Exception as e:
        logger.error(f"Error guardando {file_path}: {e}")
        return None


#guarda en archivo
def subirBucket():
    folder_path = os.path.join(folder)
    try:

        comando = ["aws", "s3", "sync", folder_path, f"s3://ic-tec-dataset/{carpeta_grupo}/"]

        result = subprocess.run(comando, shell=True, capture_output=True, text=True) 

    except Exception as e:
        logger.error(f"Error subiendo al bucket: {e}")
        return None



def main():
    global cursoId
    for category in categories:
        url = f'{urlBase}{category}'
        htmlBase = obtenerBusqueda(url)
        cursos = obtenerLinks(htmlBase)
        for curso in cursos:
            htmlCurso = obtenerProductos(curso)
            descargarHtml(htmlCurso, cursoId)
            cursoId += 1
            time.sleep(1)

if __name__ == "__main__":
    main()
