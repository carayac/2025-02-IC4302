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
MONGO_URI = "mongodb+srv://dbUser:B1b5xCdAOZDVfjcC@productssearch.sao2plc.mongodb.net/ProductsSearch?appName=ProductsSearch"
INGESTION_COLLECTION = "ingestion"

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

# DOWNLOAD HTML FROM S3
def download_html_from_s3(file_key: str) -> str:
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=file_key)
        return obj["Body"].read().decode("utf-8")
    except Exception as e:
        logger.error(f"Error downloading {file_key} from S3: {e}")
        return None

# PARSE COURSE DATA
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
        "certificate_info": None,
        "authorComment": None,
        "reviews": [],
        "rating_value": None,
        "date_extracted": datetime.utcnow().strftime("%d/%m/%Y")
    }

    # JSON-LD Extraction
    json_ld_tag = soup.find("script", type="application/ld+json")
    if json_ld_tag and json_ld_tag.string:
        try:
            cleaned = json_ld_tag.string.strip().replace("// <![CDATA[", "").replace("// ]]>", "")
            ld_data = json.loads(cleaned)
            if isinstance(ld_data, list):
                ld_data = ld_data[0]

            # Basic info
            data["title"] = ld_data.get("name")
            desc = ld_data.get("description")
            if desc:
                data["description"] = BeautifulSoup(desc, "lxml").get_text(" ", strip=True)
            data["image"] = ld_data.get("image")

            offers = ld_data.get("offers", {})
            data["price"] = float(offers.get("price", 0.0))
            data["currency"] = offers.get("priceCurrency", "USD")

            # Reviews
            for r in ld_data.get("review", []):
                author = "Anónimo"
                if isinstance(r.get("author"), dict):
                    author = r["author"].get("name", "Anónimo")
                elif isinstance(r.get("author"), str):
                    author = r["author"]

                comment = r.get("description") or r.get("reviewBody")
                rating = None
                if "reviewRating" in r and isinstance(r["reviewRating"], dict):
                    val = r["reviewRating"].get("ratingValue")
                    try:
                        rating = float(val)
                    except Exception:
                        pass

                date = None
                if r.get("datePublished"):
                    try:
                        date = datetime.strptime(r["datePublished"], "%Y-%m-%d").strftime("%d/%m/%Y")
                    except Exception:
                        date = r["datePublished"]

                data["reviews"].append({
                    "user": author or "Anónimo",
                    "comment": comment,
                    "rating": rating,
                    "date": date
                })

            if "aggregateRating" in ld_data:
                try:
                    data["rating_value"] = float(ld_data["aggregateRating"]["ratingValue"])
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Error parsing JSON-LD in {filename}: {e}")

    # Title fallback
    if not data["title"]:
        title_tag = soup.find("h1") or soup.find("title")
        if title_tag:
            data["title"] = title_tag.get_text(strip=True)

    # Description fallback
    if not data["description"]:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            data["description"] = meta_desc["content"]
        else:
            p_tag = soup.find("p")
            if p_tag:
                data["description"] = p_tag.get_text(" ", strip=True)

    # Image fallback
    if not data["image"]:
        meta_img = soup.find("meta", property="og:image")
        if meta_img and meta_img.get("content"):
            data["image"] = meta_img["content"]

    # Categories
    related_block = soup.find("div", class_="t-related")
    if related_block:
        h4_tag = related_block.find("h4")
        if h4_tag:
            data["general_category"] = h4_tag.get_text(strip=True)

    # Specific category (Área, Categoría, Tema)
    full_text = soup.get_text(" ", strip=True)
    area_match = re.search(r"(Área|Categoria|Categoría|Tema)\s*[:\-]\s*([A-Za-zÁÉÍÓÚáéíóúñÑ ]+)", full_text, re.IGNORECASE)
    if area_match:
        data["specific_category"] = area_match.group(2).strip()

    # Stats (students + rating)
    stats = soup.find("div", class_="statsc")
    if stats:
        text = stats.get_text(" ", strip=True)
        numbers = re.findall(r"\d+", text)
        if numbers:
            if len(numbers) > 5:  # Example: "495689" (rating + students)
                data["rating_value"] = float(str(numbers[0])[0])
                data["students"] = int(str(numbers[0])[1:])
            else:
                data["students"] = int(numbers[0])

    # Certificate info
    cert = soup.find("div", class_="st-certificate")
    if cert:
        data["certificate_info"] = cert.get_text(" ", strip=True)

    # Author comment
    author_block = soup.find("div", class_="st-author")
    if author_block:
        text = author_block.get_text(" ", strip=True)
        text = text.replace("Información del autor", "").strip()
        data["authorComment"] = text

    return data


def process_message(ch, method, properties, body):
    """Process message from controller queue."""
    if not body or not body.strip():
        logger.warning("Empty message received, skipping.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    file_key = body.decode("utf-8").strip()
    filename = os.path.basename(file_key)
    logger.info(f"Processing HTML file: {file_key}")

    coll = mongo_collection()

    #Mark as started
    coll.update_one({"_id": file_key}, {"$set": {"processing": "started"}}, upsert=True)

    html_content = download_html_from_s3(file_key)
    if not html_content:
        logger.error(f"Failed to download {file_key}, skipping.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    data = extract_course_data(html_content, filename)

    # Save JSON
    raw_dir = os.path.join(SHARED_VOLUME_PATH, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    json_path = os.path.join(raw_dir, filename.replace(".html", ".json"))
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON file saved: {json_path}")

    #Mark as completed
    coll.update_one({"_id": file_key}, {"$set": {"processing": "completed"}})

    # Publish to entity queue
    msg_to_entity = {"s3Key": file_key, "jsonPath": json_path}
    ch.basic_publish(
        exchange="",
        routing_key=RABBITMQ_QUEUE_ENTITY,
        body=json.dumps(msg_to_entity)
    )
    logger.info(f"Published to {RABBITMQ_QUEUE_ENTITY}: {msg_to_entity}")

    ch.basic_ack(delivery_tag=method.delivery_tag)


# MAIN
def main():
    logger.info("Starting BeautifulSoup Parser")
    connection, channel = connect_rabbitmq()
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=RABBITMQ_QUEUE_HTML, on_message_callback=process_message)

    try:
        logger.info(f"Listening for messages from {RABBITMQ_QUEUE_HTML}")
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Stopping parser")
        channel.stop_consuming()
    finally:
        connection.close()
        logger.info("RabbitMQ connection closed.")

if __name__ == "__main__":
    main()


