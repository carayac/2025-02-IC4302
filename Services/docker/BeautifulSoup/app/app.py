import os
import re
import json
import boto3
import pika
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from pymongo import MongoClient

# LOGGING CONFIGURATION
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("beautifulsoup_parser")

# ENVIRONMENT VARIABLES
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET")

RABBITMQ_HOST = os.getenv("RABBITMQ")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS")
RABBITMQ_QUEUE_HTML = os.getenv("RABBITMQ_QUEUE_HTML")
RABBITMQ_QUEUE_ENTITY = os.getenv("RABBITMQ_QUEUE_ENTITY")

SHARED_VOLUME_PATH = os.getenv("SHARED_VOLUME_PATH", "/xdata")

# MongoDB
MONGO_URI = os.getenv("MONGO_URI")
INGESTION_COLLECTION = os.getenv("INGESTION_COLLECTION", "ingestion")

# S3 CLIENT
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

def mongo_collection():
    client = MongoClient(MONGO_URI)
    db = client.get_default_database()
    return db[INGESTION_COLLECTION]

def connect_rabbitmq():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE_HTML, durable=True)
    channel.queue_declare(queue=RABBITMQ_QUEUE_ENTITY, durable=True)
    return connection, channel


def download_html_from_s3(file_key: str) -> str:
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=file_key)
        return obj["Body"].read().decode("utf-8")
    except Exception as e:
        logger.error(f"Error downloading {file_key} from S3: {e}")
        return None

def parse_author(author_block):
    if not author_block:
        return None, None

    raw = author_block.get_text(separator=" ", strip=True)

    #Limpiar encabezados
    to_remove = [
        "Información del autor", "Información del Autor",
        "Información del", "Información  del autor",
        "Información", "autor:"
    ]
    clean = raw
    for r in to_remove:
        clean = clean.replace(r, "")
    clean = clean.strip()

    if not clean:
        return None, None

    # Caso 2: comentario largo sin nombre
    if clean.lower().startswith((
        "este curso", "en este curso", "si necesita",
        "curso ", "ha sido", "mediante"
    )):
        return None, clean

    palabras = clean.split()
    if not palabras:
        return None, None

    #separar nombre de comentario
    keywords = [
        "magíster", "profesor", "ciencias", "ingeniería",
        "aplicada", "licencia", "director", "gestión",
        "autor", "educación", "estándar"
    ]

    idx = None
    for i, p in enumerate(palabras):
        if p.lower() in keywords:
            idx = i
            break

    # Caso 3: nombre + descripción pegados
    if idx:
        name = " ".join(palabras[:idx]) or None
        comment = " ".join(palabras[idx:]) or None
        return name, comment

    if len(palabras) <= 4:
        return clean, None

    #todo comentario
    return None, clean



def extract_course_data(html: str, filename: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    data = {
        "title": None,
        "general_category": None,
        "specific_category": None,
        "description": None,
        "image": None,
        "price": 0.0,
        "currency": "USD",
        "language": "es",
        "students": None,
        "rating_value": None,
        "estimated_weeks": None,
        "hours_per_week": None,
        "certificate_info": None,
        "author": {"name": None, "comment": None},
        "reviews": [],
        "date_extracted": datetime.utcnow().strftime("%d/%m/%Y")
    }

    # JSON-LD 
    json_ld_tag = soup.find("script", type="application/ld+json")

    if json_ld_tag and json_ld_tag.string:
        try:
            cleaned = json_ld_tag.string.strip().replace("// <![CDATA[", "").replace("// ]]>", "")
            ld = json.loads(cleaned)

            if isinstance(ld, list):
                ld = ld[0]

            # Title + desc
            data["title"] = ld.get("name")

            desc = ld.get("description")
            if desc:
                data["description"] = BeautifulSoup(desc, "lxml").get_text(" ", strip=True)

            #Image
            data["image"] = ld.get("image")

            offers = ld.get("offers", {})
            data["price"] = float(offers.get("price", 0.0))
            data["currency"] = offers.get("priceCurrency", "USD")

            #rating
            if "aggregateRating" in ld:
                try:
                    data["rating_value"] = float(ld["aggregateRating"]["ratingValue"])
                except:
                    pass

            # Reviews
            for r in ld.get("review", []):
                author = "Anónimo"
                if isinstance(r.get("author"), dict):
                    author = r["author"].get("name", "Anónimo")
                elif isinstance(r.get("author"), str):
                    author = r["author"]

                comment_html = r.get("description") or r.get("reviewBody")
                if comment_html:
                    comment = BeautifulSoup(comment_html, "lxml").get_text(" ", strip=True)
                else:
                    comment = None

                rating = None
                if "reviewRating" in r and isinstance(r["reviewRating"], dict):
                    rv = r["reviewRating"].get("ratingValue")
                    try:
                        rating = float(rv)
                    except:
                        pass

                date = None
                if r.get("datePublished"):
                    try:
                        date = datetime.strptime(r["datePublished"], "%Y-%m-%d").strftime("%d/%m/%Y")
                    except:
                        date = r["datePublished"]

                data["reviews"].append({
                    "user": author or "Anónimo",
                    "comment": comment,
                    "rating": rating,
                    "date": date
                })

        except Exception as e:
            logger.warning(f"JSON-LD error in {filename}: {e}")





    # TITLE / DESCRIPTION FALLBACKS
    if not data["title"]:
        t = soup.find("h1") or soup.find("title")
        if t:
            data["title"] = t.get_text(strip=True)

    if not data["description"]:
        meta_d = soup.find("meta", {"name": "description"})
        if meta_d and meta_d.get("content"):
            data["description"] = meta_d["content"]
        else:
            p = soup.find("p")
            if p:
                data["description"] = p.get_text(" ", strip=True)

    # GENERAL CATEGORY 
    related_block = soup.find("div", class_="t-related")
    if related_block:
        h4 = related_block.find("h4")
        if h4:
            data["general_category"] = h4.get_text(strip=True)

    # SPECIFIC CATEGORY
    full_text = soup.get_text(" ", strip=True)
    area_match = re.search(
        r"(Área|Categoria|Categoría|Tema)\s*[:\-]\s*([A-Za-zÁÉÍÓÚáéíóúñÑ ]+)",
        full_text,
        re.IGNORECASE
    )
    if area_match:
        data["specific_category"] = area_match.group(2).strip()

    # Estimated weeks & hours per week
    extra_text = soup.get_text(" ", strip=True)

    w = re.search(r"(\d+)\s*semanas", extra_text, re.IGNORECASE)
    if w:
        data["estimated_weeks"] = int(w.group(1))

    hp = re.search(r"(\d+-\d+)\s*horas", extra_text, re.IGNORECASE)
    if hp:
        data["hours_per_week"] = hp.group(1)


    #EXTRACT RATING + STUDENTS
    def _to_float(num_str):
        try:
            return float(num_str.replace(",", "."))
        except:
            return None

    def _to_int_digits(num_str):
        digits = re.sub(r"[^\d]", "", num_str)
        try:
            return int(digits) if digits else None
        except:
            return None

    rating_dom = None
    students_dom = None

    stats = soup.select_one("div.statsc")
    if stats:
        opinions_text = None
        for div in stats.select("div"):
            txt = div.get_text(" ", strip=True)
            if "opinion" in txt.lower():
                opinions_text = txt
                break
        if opinions_text:
            m = re.search(r"(\d+(?:[.,]\d+)?)", opinions_text)
            if m:
                rating_dom = _to_float(m.group(1))

        students_text = None
        for div in stats.select("div"):
            txt = div.get_text(" ", strip=True)
            if "estudiante" in txt.lower():
                students_text = txt
                break
        if students_text:
            m = re.search(r"([\d\.,]+)", students_text)
            if m:
                students_dom = _to_int_digits(m.group(1))

    if rating_dom is not None:
        data["rating_value"] = rating_dom

    if students_dom is not None:
        data["students"] = students_dom
    if data["students"] is None:
        m = re.search(r"([\d\.,]+)\s*estudiantes?", full_text, re.IGNORECASE)
        if m:
            data["students"] = _to_int_digits(m.group(1))

    # CERTIFICATE INFO
    cert = soup.find("div", class_="st-certificate")
    if cert:
        data["certificate_info"] = cert.get_text(" ", strip=True)

    #AUTHOR DIC
    author_block = soup.find("div", class_="st-author")
    name, comment = parse_author(author_block)

    if name is None:
        name = "Edutin Academy"

    data["author"] = {
        "name": name,
        "comment": comment
    }

    return data



def process_message(ch, method, properties, body):

    if not body or not body.strip():
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    raw = body.decode("utf-8").strip()

    file_key = None
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and "id" in parsed:
            file_key = parsed["id"]
        elif isinstance(parsed, str):
            file_key = parsed
    except:
        file_key = raw

    filename = os.path.basename(file_key)

    coll = mongo_collection()
    coll.update_one({"_id": file_key}, {"$set": {"processing": "started"}}, upsert=True)

    html = download_html_from_s3(file_key)
    if not html:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    data = extract_course_data(html, filename)

    raw_dir = os.path.join(SHARED_VOLUME_PATH, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    json_path = os.path.join(raw_dir, filename.replace(".html", ".json"))

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    coll.update_one({"_id": file_key}, {"$set": {"processing": "completed"}})

    msg_to_entity = {"s3Key": file_key, "jsonPath": json_path}
    ch.basic_publish(exchange="", routing_key=RABBITMQ_QUEUE_ENTITY, body=json.dumps(msg_to_entity))

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection, channel = connect_rabbitmq()
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=RABBITMQ_QUEUE_HTML, on_message_callback=process_message)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()


if __name__ == "__main__":
    main()


