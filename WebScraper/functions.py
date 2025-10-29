import requests
import os
import sys
import logging
import re
import time
from selenium import webdriver

logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

#Variables
headers = {"User-Agent": "Mozilla/5.0"}  #para evitar ser detectado como bot
url = "https://app.edutin.com/search/courses?q=programacion"
folder = "productos"

#obtiene html base
def obtenerBusqueda(url):
    from selenium import webdriver
    driver = webdriver.Chrome()
    driver.get(url)
    driver.implicitly_wait(5)
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

    cursos = [l for l in links if not any(ext in l for ext in [".jpg", ".png", ".svg", "facebook", "twitter"])]
    return list(set(cursos))[:500]  # eliminar duplicados y solo los primeros 500


#guarda en archivo
def descargarHtml(html, num):
    if not html:
        logger.warning(f"HTML vacío para el curso #{num}")
        return
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(os.path.expanduser("~"), "Downloads", folder, f"curso_{num:03d}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info(f"Guardado: {file_path}")


def main():
    htmlBase = obtenerBusqueda(url)
    cursos = obtenerLinks(htmlBase)
    for num, curso in enumerate (cursos, start = 1):
        htmlCurso = obtenerProductos(curso)
        descargarHtml(htmlCurso, num)
        time.sleep(1)

if __name__ == "__main__":
    main()
