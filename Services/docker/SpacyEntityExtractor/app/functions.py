import os
import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, List
import re

import pika
from pymongo import MongoClient
import spacy  # SPACY para procesamiento de lenguaje natural entities


MONGO_URI = os.getenv("MONGO_URI")
INGESTION_COLLECTION = os.getenv("INGESTION_COLLECTION")

# RabbitMQ 
RABBIT_HOST = os.getenv("RABBITMQ")
RABBIT_USER = os.getenv("RABBITMQ_USER")
RABBIT_PASS = os.getenv("RABBITMQ_PASS")
RABBIT_QUEUE_NER = os.getenv("RABBITMQ_QUEUE")

# PVC de writeMany
RAW_DIR = os.getenv("RAW_DIR")
AUGMENTED_DIR = os.getenv("AUGMENTED_DIR")

# Logging de Python
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("spacy-ner")

# Definicion de fecha actual para colección
def now() -> str:
    return datetime.now(timezone.utc).isoformat()

#Conexion a MongoDB
def mongo_collection():
    client = MongoClient(MONGO_URI)
    db = client.get_default_database()
    return db[INGESTION_COLLECTION]


#Conexion a RabbitMQ
def rabbit_channel():
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(host=RABBIT_HOST, credentials=credentials)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.queue_declare(queue=RABBIT_QUEUE_NER, durable=True)
    ch.basic_qos(prefetch_count=1)
    return conn, ch

def path_from_key(base_dir: str, s3_key: str) -> str:
    
    #Nombre del archivo
    filename = os.path.basename(s3_key)

    # nombre sin extension 
    name, _ = os.path.splitext(filename)
    augmented_name = name + ".json"
    return os.path.join(base_dir, augmented_name)


# Actualiza el estado de la extracción de entidades en MongoDB
def entities_status(coll, doc_id: str, value: str, error: str | None = None):

    update = {
        "entitiesExtraction": value
    }
    #En caso de error, agregar el mensaje de error a la colección
    if value == "error" and error:
        update["entitiesExtractionError"] = error

    # Actualiza la colección según el doc_id
    coll.update_one({"_id": doc_id}, {"$set": update})



# Carga del modelo spaCy para la entities recognition
def spacy_load():
    try:
        return spacy.load("es_core_news_lg") #Modelo mediano en español
    except Exception:
        log.warning("Modelo es_core_news_md no disponible, usando es_core_news_lg.")
        return spacy.load("es_core_news_lg") #Modelo grande en español

# Se guarda el pipeline del modelo elegido 
NLP = spacy_load()

# Allowed labels para evitar entity MISC
ALLOWED_LABELS = {"PER","ORG","LOC","GPE", "DATE",     
    "TIME","MONEY","PERCENT","QUANTITY","ORDINAL","CARDINAL",}

#Normalización del json para mejorar el reconocimiento de entidades
def normalize_text(text: str) -> str:

    if not text:
        return ""
    # unifica saltos de linea 
    text = text.replace("\r", " ").replace("\n", " ")
    # quita espacios multiples
    text = re.sub(r"\s{2,}", " ", text)
    # recorta
    text = text.strip()
    return text



# Funcion para realizar la extracción de entidades que devuelve una lista de diccionarios con type y value extraidos
def extract_entities(text: str) -> List[Dict[str, str]]:

    text = normalize_text(text)
    doc = NLP(text) # Doc Objeto con toda la información del texto que fue procesado

   # Recorre cada entidad y extrae text y label_ (texto y tipo de entidad ORG, PRODUCTO)
    ents = [{"type": ent.label_, "value": ent.text} for ent in doc.ents]

    # Depuración de duplicacion de entidades
    repeted = set()
    out: List[Dict[str, str]] = []

    # Recorre cada una de las entidades extraidas
    for e in ents:
        label = e["type"]
        val = e["value"].strip()  # Normaliza

        if label not in ALLOWED_LABELS:
            continue

        if "\n" in val: #descartar entidades con salto de linea
            continue

        if len(val.split()) > 8:    #descartar entidades con más de 8 palabras
            continue

        key = (label, val.lower())
        
        # Si la entidad no está en el conjunto de vistas entonces se agrega, de lo contrario se ignora
        if key in repeted:
            continue
        repeted.add(key)
        out.append({"type": e["type"], "value": val})
    return out


# Manejo del mensaje publicado por el BeautifulSoup
def message(coll, msg: dict):

    
    s3_key = msg["_id"]
    raw_path = msg["jsonPath"] 
    doc_id = s3_key  # Usar s3_key como _id en MongoDB porque es lo equivalente

    # Actualización en coleccion a: Extracción de Entidades iniciada
    entities_status(coll, doc_id, "started")
    log.info("entitiesExtraction iniciado para %s", doc_id)

    #Se busca el archivo guardado en el volumen
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"RAW no encontrado: {raw_path}")

    #Lectura del json de la carpeta raw
    with open(raw_path, "r", encoding="utf-8") as f:
        raw_doc = json.load(f)

    # Se contruye el texto que analizará spicy 
    blocks = []
    for k in (
        "title",
        "general_category",
        "specific_category",
        "description",
        "price",
        "students",
        "certificate_info",
        "authorComment",
    ):
        v = raw_doc.get(k)
        if v is not None:
            blocks.append(str(v))

    reviews = raw_doc.get("reviews")
    if isinstance(reviews, list):
        for r in reviews:
            #lee user de reviews
            user = r.get("user")
            if isinstance(user, str):
                blocks.append(user)
            #lee coments de reviews
            comment = r.get("comment")
            if isinstance(comment, str):
                blocks.append(comment)
            #lee rating de reviews
            rating = r.get("rating")
            if rating is not None:
                blocks.append(str(rating))
            #lee date de reviews
            date = r.get("date")
            if isinstance(date, str):
                blocks.append(date)

    text = "\n".join(blocks).strip()
    #Extracción de entidades con el texto concatenado
    entities = extract_entities(text) if text else []

    #Despues de extracción
    augmented = dict(raw_doc)   #Copia el json original
    augmented["entities"] = entities    #Agrega un campo entities

    # Guarda el doc en el volumen compartido
    os.makedirs(AUGMENTED_DIR, exist_ok=True)
    out_path = path_from_key(AUGMENTED_DIR, s3_key)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(augmented, f, ensure_ascii=False, indent=2)

    # Se actualiza el estado a: Extracción de Entidades completada
    entities_status(coll, doc_id, "completed")
    log.info("GUARDADO: %s (# Entidades=%d)", out_path, len(entities))


def run():
    log.info("Spacy Entity Extractor iniciado.")
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(AUGMENTED_DIR, exist_ok=True)

    #conexiones
    coll = mongo_collection()
    conn, ch = rabbit_channel()

    def callback(ch_, method, properties, body):
        try:
            msg = json.loads(body.decode("utf-8"))
            message(coll, msg)
            ch_.basic_ack(delivery_tag=method.delivery_tag) #mensaje procesado, puede ser borrado de  cola
        except Exception as e:
            log.error("Error procesando mensaje:\n%s", traceback.format_exc())
            
            try:
                parsed = json.loads(body.decode("utf-8"))
                s3_key = parsed.get("_id", "unknown")
                entities_status(coll, s3_key, "error", str(e))    #mapear error en colección
            except Exception:
                pass
            
            #quita mensaje de cola sin reintento por haber tirado error
            ch_.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    ch.basic_consume(queue=RABBIT_QUEUE_NER, on_message_callback=callback)
    log.info("Esperando mensajes en '%s'…", RABBIT_QUEUE_NER)

    #Espera mensajes hasta que se interrumpa el proceso
    try:
        ch.start_consuming()
    finally:
        try:
            conn.close()
        except Exception:
            pass
        log.info("Conexión RabbitMQ cerrada.")