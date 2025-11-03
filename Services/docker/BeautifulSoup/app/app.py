import os
import re
import json
import boto3
import pika
import logging
from bs4 import BeautifulSoup
from datetime import datetime

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

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)


# RABBITMQ CONNECTION
def connect_rabbitmq():
    """Establish connection with RabbitMQ and declare required queues."""
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE_HTML, durable=True)
    channel.queue_declare(queue=RABBITMQ_QUEUE_ENTITY, durable=True)
    return connection, channel

# DOWNLOAD HTML FROM S3
def download_html_from_s3(file_key: str) -> str:
    """Downloads an HTML file from S3"""
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=file_key)
        return obj["Body"].read().decode("utf-8")
    except Exception as e:
        logger.error(f"Error downloading {file_key} from S3: {e}")
        return None

def extract_course_data(html: str, filename: str) -> dict:
    """Extracts course information using BeautifulSoup"""
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

    #JSON-LD 
    json_ld_tag = soup.find("script", type="application/ld+json")
    if json_ld_tag and json_ld_tag.string:
        try:
            cleaned = json_ld_tag.string.strip()
            cleaned = cleaned.replace("// <![CDATA[", "").replace("// ]]>", "")
            ld_data = json.loads(cleaned)
            if isinstance(ld_data, list):
                ld_data = ld_data[0]

            # Title and description
            data["title"] = ld_data.get("name")
            desc = ld_data.get("description")
            if desc:
                data["description"] = BeautifulSoup(desc, "lxml").get_text(" ", strip=True)

            # Image
            data["image"] = ld_data.get("image")

            # Price and currency
            offers = ld_data.get("offers", {})
            data["price"] = float(offers.get("price", 0.0))
            data["currency"] = offers.get("priceCurrency", "USD")

            # Reviews
            reviews = ld_data.get("review", [])
            if isinstance(reviews, list):
                for r in reviews:
                    author = "Anónimo"
                    if isinstance(r.get("author"), dict):
                        author = r["author"].get("name", "Anónimo")
                    elif isinstance(r.get("author"), str):
                        author = r["author"]

                    review_text = r.get("description") or r.get("reviewBody") or None
                    rating_value = None
                    if "reviewRating" in r and isinstance(r["reviewRating"], dict):
                        val = r["reviewRating"].get("ratingValue")
                        try:
                            rating_value = float(val)
                        except (ValueError, TypeError):
                            rating_value = None

        
                    review_date = r.get("datePublished")
                    formatted_date = None
                    if review_date:
                        try:
                            formatted_date = datetime.strptime(review_date, "%Y-%m-%d").strftime("%d/%m/%Y")
                        except ValueError:
                            formatted_date = review_date  # keep original if parsing fails

                    data["reviews"].append({
                        "user": author or "Anónimo",
                        "comment": review_text,
                        "rating": rating_value,
                        "date": formatted_date
                    })

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

    # General category
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

    #RATING Y STUDENTS
    stats = soup.find("div", class_="statsc")
    if stats:
        # Buscar rating (ej. "4.8" antes de "opiniones")
        rating_div = stats.find(string=re.compile(r"^\s*\d+[.,]?\d*\s*$"))
        if rating_div:
            try:
                data["rating_value"] = float(rating_div.strip().replace(",", "."))
            except ValueError:
                pass

        # Buscar número de estudiantes
        students_div = stats.find(string=re.compile(r"estudiantes", re.IGNORECASE))
        if students_div:
            match = re.search(r"(\d+[.,]?\d*)", students_div)
            if match:
                num_str = match.group(1).replace(".", "").replace(",", "")
                try:
                    data["students"] = int(num_str)
                except ValueError:
                    pass

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
    """Processes each message received from controller."""
    file_key = body.decode("utf-8")
    filename = os.path.basename(file_key)
    logger.info(f"Processing HTML file: {file_key}")

    html_content = download_html_from_s3(file_key)
    if not html_content:
        logger.error(f"Failed to download {file_key}, skipping.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    data = extract_course_data(html_content, filename)

    # Save JSON to shared volume
    raw_dir = os.path.join(SHARED_VOLUME_PATH, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    json_path = os.path.join(raw_dir, filename.replace(".html", ".json"))

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON file saved: {json_path}")
    except Exception as e:
        logger.error(f"Error saving JSON for {filename}: {e}")

    # Publish message to entity queue
    try:
        ch.basic_publish(
            exchange="",
            routing_key=RABBITMQ_QUEUE_ENTITY,
            body=json_path
        )
        logger.info(f"Published to {RABBITMQ_QUEUE_ENTITY}: {json_path}")
    except Exception as e:
        logger.error(f"Error publishing to RabbitMQ: {e}")

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
