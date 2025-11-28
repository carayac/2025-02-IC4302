import os
import kagglehub
from kagglehub import KaggleDatasetAdapter
import pandas as pd
from os import getenv
import psycopg2
import psycopg2.pool
import sys
import mysql.connector
from mysql.connector import pooling
from elasticsearch import Elasticsearch, helpers
from opensearchpy import OpenSearch, helpers as os_helpers
from neo4j import GraphDatabase
import requests
from pymongo import MongoClient
from pymongo.errors import PyMongoError



#Variables de entorno, enable en el deployment.yaml
POSTGRES_ENABLE = os.getenv("POSTGRES_ENABLE", "true").lower() == "true"
MARIADB_ENABLE = os.getenv("MARIADB_ENABLE", "true").lower() == "true"
ELASTICSEARCH_ENABLE = os.getenv("ELASTICSEARCH_ENABLE", "true").lower() == "true"
OPENSEARCH_ENABLE = os.getenv("OPENSEARCH_ENABLE", "true").lower() == "true"
CHROMADB_ENABLE = os.getenv("CHROMADB_ENABLE", "true").lower() == "true"
MONGO_ENABLE = os.getenv("MONGO_ENABLE", "true").lower() == "true"
COUCHDB_ENABLE = os.getenv("COUCHDB_ENABLE", "true").lower() == "true"
NEO4J_ENABLE = os.getenv("NEO4J_ENABLE", "false").lower() == "true"



if POSTGRES_ENABLE:
    # Variables de entorno
    POSTGRES = getenv("POSTGRES")
    POSTGRES_USER = getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")
    POSTGRES_DB = getenv("POSTGRES_DB")

if MARIADB_ENABLE:
    # Variables de entorno
    MARIADB = getenv("MARIADB")
    MARIADB_USER = getenv("MARIADB_USER")
    MARIADB_PASS = getenv("MARIADB_PASS")
    MARIADB_DB = getenv("MARIADB_DB")

if ELASTICSEARCH_ENABLE:
    # Variables de entorno
    ELASTIC = getenv("ELASTIC")        
    ELASTIC_USER = getenv("ELASTIC_USER")
    ELASTIC_PASS = getenv("ELASTIC_PASS")
    ES_PORT = getenv("ES_PORT", "9200")

if CHROMADB_ENABLE:
    CHROMA_ENDPOINT = getenv("CHROMA_ENDPOINT", "http://localhost:8000")
    CHROMA_COLLECTION = getenv("CHROMA_COLLECTION", "animals")
    CHROMA_EMBED_MODEL = getenv("CHROMA_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

if OPENSEARCH_ENABLE:
    OPENSEARCH_ENDPOINT = getenv("OPENSEARCH_ENDPOINT", "http://localhost:9200")
    OPENSEARCH_USER = getenv("OPENSEARCH_USER", "admin")
    OPENSEARCH_PASS = getenv("OPENSEARCH_PASS")
    OPENSEARCH_COLLECTION = getenv("OPENSEARCH_COLLECTION", "animales")

if MONGO_ENABLE:
    MONGO_HOST = getenv("MONGO_HOST")
    MONGO_PORT = getenv("MONGO_PORT")
    MONGO_DB = getenv("MONGO_DB")
    MONGO_COLLECTION = getenv("MONGO_COLLECTION")
    MONGO_USER = getenv("MONGO_USER")
    MONGO_PASS = getenv("MONGO_PASS")
    MONGO_AUTH_DB = getenv("MONGO_AUTH_DB")
    MONGO_URI = (
        f"mongodb://{MONGO_USER}:{MONGO_PASS}@"
        f"{MONGO_HOST}:{MONGO_PORT}/?authSource={MONGO_AUTH_DB}")
    
if COUCHDB_ENABLE:
    COUCHDB_HOST = getenv("COUCHDB_HOST")
    COUCHDB_PORT = getenv("COUCHDB_PORT")
    COUCHDB_DB = getenv("COUCHDB_DB")
    COUCHDB_USER = getenv("COUCHDB_USER")
    COUCHDB_PASS = getenv("COUCHDB_PASS")

if NEO4J_ENABLE:
    NEO4J_HOST = getenv("NEO4J_HOST", "databases-neo4j")
    NEO4J_PORT = getenv("NEO4J_PORT", "7687")  # puerto bolt
    NEO4J_USER = getenv("NEO4J_USER", "neo4j")
    NEO4J_PASS = getenv("NEO4J_PASS")
    NEO4J_DB   = getenv("NEO4J_DB", "neo4j")




def load_dataset():
    try:
        df = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            "iamsouravbanerjee/animal-information-dataset",
            "Animal Dataset.csv"
        )
        print(f"Dataset cargado: {len(df)} registros")
        return df
    except Exception as e:
        print(f"Error cargando dataset: {e}")
        raise

#---------------------------------------PostgreSQL-------------------------------------
if POSTGRES_ENABLE:
    # Crear pool de conexiones PostgreSQL
    try:
        pg_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            host=POSTGRES,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB
        )
        print("Pool de conexiones PostgreSQL creado")
    except Exception as e:
        print(f"Error creando pool PostgreSQL: {e}")
        sys.exit(1)

def execute_postgress_from_file():    
    # Construir la ruta al archivo
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(script_dir, 'schemas', 'postgres.sql')    
    try:
        with open(schema_path, 'r', encoding='utf-8') as file:
            schema_sql = file.read()
        print("Archivo leído correctamente")
    except FileNotFoundError:
        print(f"Archivo no encontrado en: {schema_path}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    conn = pg_pool.getconn()
    cur = conn.cursor()
    
    try:
        cur.execute(schema_sql)
        conn.commit()
        print("Tablas creadas exitosamente en PostgreSQL")
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        cur.close()
        pg_pool.putconn(conn)

def insert_data_postgres(df):    
    conn = pg_pool.getconn()
    cur = conn.cursor()
    
    try:
        for index, row in df.iterrows():
            cur.execute("""
                INSERT INTO dieta (tipo_dieta) VALUES (%s) 
                ON CONFLICT (tipo_dieta) DO NOTHING
            """, (row["Diet"],))
            cur.execute("SELECT id FROM dieta WHERE tipo_dieta=%s", (row["Diet"],))
            dieta_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO familia (nombre_familia) VALUES (%s) 
                ON CONFLICT (nombre_familia) DO NOTHING
            """, (row["Family"],))
            cur.execute("SELECT id FROM familia WHERE nombre_familia=%s", (row["Family"],))
            familia_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO animal (nombre, altura_cm, peso_kg, color, esperanza_vida_años, dieta_id, familia_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (
                row["Animal"], row["Height (cm)"], row["Weight (kg)"], row["Color"],
                row["Lifespan (years)"], dieta_id, familia_id
            ))
            animal_id = cur.fetchone()[0]

            habitats = [h.strip() for h in str(row["Habitat"]).split(",") if h.strip()]
            for h in habitats:
                if h and h.lower() != 'nan':
                    cur.execute("""
                        INSERT INTO habitat (nombre_habitat) VALUES (%s) 
                        ON CONFLICT (nombre_habitat) DO NOTHING
                    """, (h,))
                    cur.execute("SELECT id FROM habitat WHERE nombre_habitat=%s", (h,))
                    habitat_id = cur.fetchone()[0]
                    cur.execute("""
                        INSERT INTO animal_habitat (animal_id, habitat_id) VALUES (%s, %s) 
                        ON CONFLICT (animal_id, habitat_id) DO NOTHING
                    """, (animal_id, habitat_id))

            predadores = [p.strip() for p in str(row["Predators"]).split(",") if p.strip()]
            for p in predadores:
                if p and p.lower() != 'nan':
                    cur.execute("""
                        INSERT INTO predador (nombre_predador) VALUES (%s) 
                        ON CONFLICT (nombre_predador) DO NOTHING
                    """, (p,))
                    cur.execute("SELECT id FROM predador WHERE nombre_predador=%s", (p,))
                    predador_id = cur.fetchone()[0]
                    cur.execute("""
                        INSERT INTO animal_predador (animal_id, predador_id) VALUES (%s, %s) 
                        ON CONFLICT (animal_id, predador_id) DO NOTHING
                    """, (animal_id, predador_id))

            cur.execute("""
                INSERT INTO info_extra (animal_id, velocidad_prom_kmh, velocidad_max_kmh, paises_encontrado,
                estado_conservacion, gestacion_dias, estructura_social, crias_por_parto)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                animal_id, row["Average Speed (km/h)"], row["Top Speed (km/h)"], row["Countries Found"],
                row["Conservation Status"], row["Gestation Period (days)"], row["Social Structure"], row["Offspring per Birth"]
            ))

        conn.commit()
        print(f"Registros insertados exitosamente")
        return True
        
    except Exception as e:
        print(f"Error insertando datos: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        pg_pool.putconn(conn)

#-------------------------------------Maria DB------------------------------------- 
mariadb_pool = None

# Crear conexion MariaDB
def conection_mariadb():
    global mariadb_pool
    try:
        # Conexión inicial sin base seleccionada
        conn = mysql.connector.connect(
            host=MARIADB,
            user=MARIADB_USER,
            password=MARIADB_PASS,
            charset="utf8mb4",
            collation="utf8mb4_general_ci"
        )
        cur = conn.cursor()
        # Crear la base de datos con charset y collation explícitos
        cur.execute(f"""
            CREATE DATABASE IF NOT EXISTS {MARIADB_DB}
            DEFAULT CHARACTER SET utf8mb4
            DEFAULT COLLATE utf8mb4_general_ci;
        """)
        conn.commit()
        cur.close()
        conn.close()
        print(f"Base de datos {MARIADB_DB} creada o ya existente.")
    except Exception as e:
        print(f"Error creando la base de datos: {e}")
        sys.exit(1)

    # Crear pool de conexiones 
    try:
        mariadb_pool = pooling.MySQLConnectionPool(
            pool_name="mariadb_pool",
            pool_size=5,
            host=MARIADB,
            user=MARIADB_USER,
            password=MARIADB_PASS,
            database=MARIADB_DB,
            charset='utf8mb4',
            collation='utf8mb4_general_ci',
            autocommit=True
        )
        print("Pool de conexiones MariaDB creado")
    except Exception as e:
        print(f"Error creando pool MariaDB: {e}")
        sys.exit(1)


def execute_MariaDB_from_file():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(script_dir, 'schemas', 'mariadb.sql')    
    try:
        with open(schema_path, 'r', encoding='utf-8') as file:
            schema_sql = file.read()
        print("Archivo leído correctamente")
    except FileNotFoundError:
        print(f"Archivo no encontrado en: {schema_path}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    conn = mariadb_pool.get_connection()
    cur = conn.cursor()
    
    try:
        for statement in schema_sql.split(";"):
            stmt = statement.strip()
            if stmt:
                cur.execute(stmt)
        conn.commit()
        print("Tablas creadas exitosamente en MariaDB")
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error creando tablas de MariaDB: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def insert_data_mariadb(df):
    conn = mariadb_pool.get_connection()
    cur = conn.cursor()
    try:
        for index, row in df.iterrows():
            cur.execute("""
                INSERT IGNORE INTO dieta (tipo_dieta) VALUES (%s)
            """, (row["Diet"],))
            cur.execute("SELECT id FROM dieta WHERE tipo_dieta=%s", (row["Diet"],))
            dieta_id = cur.fetchone()[0]

            cur.execute("""
                INSERT IGNORE INTO familia (nombre_familia) VALUES (%s)
            """, (row["Family"],))
            cur.execute("SELECT id FROM familia WHERE nombre_familia=%s", (row["Family"],))
            familia_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO animal (nombre, altura_cm, peso_kg, color, esperanza_vida_años, dieta_id, familia_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                row["Animal"], row["Height (cm)"], row["Weight (kg)"], row["Color"],
                row["Lifespan (years)"], dieta_id, familia_id
            ))
            animal_id = cur.lastrowid  

            habitats = [h.strip() for h in str(row["Habitat"]).split(",") if h.strip()]
            for h in habitats:
                if h and h.lower() != 'nan':
                    cur.execute("""
                        INSERT IGNORE INTO habitat (nombre_habitat) VALUES (%s)
                    """, (h,))
                    cur.execute("SELECT id FROM habitat WHERE nombre_habitat=%s", (h,))
                    habitat_id = cur.fetchone()[0]
                    cur.execute("""
                        INSERT IGNORE INTO animal_habitat (animal_id, habitat_id) VALUES (%s, %s)
                    """, (animal_id, habitat_id))

            predadores = [p.strip() for p in str(row["Predators"]).split(",") if p.strip()]
            for p in predadores:
                if p and p.lower() != 'nan':
                    cur.execute("""
                        INSERT IGNORE INTO predador (nombre_predador) VALUES (%s)
                    """, (p,))
                    cur.execute("SELECT id FROM predador WHERE nombre_predador=%s", (p,))
                    predador_id = cur.fetchone()[0]
                    cur.execute("""
                        INSERT IGNORE INTO animal_predador (animal_id, predador_id) VALUES (%s, %s)
                    """, (animal_id, predador_id))

            cur.execute("""
                INSERT INTO info_extra (animal_id, velocidad_prom_kmh, velocidad_max_kmh, paises_encontrado,
                estado_conservacion, gestacion_dias, estructura_social, crias_por_parto)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                animal_id, row["Average Speed (km/h)"], row["Top Speed (km/h)"], row["Countries Found"],
                row["Conservation Status"], row["Gestation Period (days)"], row["Social Structure"], row["Offspring per Birth"]
            ))

        conn.commit()
        print("Registros insertados exitosamente en MariaDB")
        return True

    except Exception as e:
        conn.rollback()
        print(f"Error insertando datos en MariaDB: {e}")
        return False
    finally:
        cur.close()
        conn.close()

#-------------------------------------Elastic Search-------------------------------------
# Crear conexión Elasticsearch
def get_connectionElastic():
    try:
        conn = Elasticsearch(
            [f"http://{ELASTIC}:{ES_PORT}"],
            basic_auth=(ELASTIC_USER, ELASTIC_PASS)
        )
        if not conn.ping():
            raise Exception("No se pudo conectar a Elasticsearch")
        return conn
    except Exception as e:
        print(f"Error creando conexión Elasticsearch: {e}")
        sys.exit(1)


def create_index_elastic():
    index_name = "animals"
    es = get_connectionElastic()
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body={
            "mappings": {
                "properties": {
                    "name": {"type": "keyword"},
                    "height_cm": {"type": "keyword"},
                    "weight_kg": {"type": "keyword"},
                    "color": {"type": "keyword"},
                    "lifespan_years": {"type": "keyword"},
                    "diet": {"type": "keyword"},
                    "habitat": {"type": "text"},
                    "predators": {"type": "text"},
                    "average_speed_kmh": {"type": "keyword"},
                    "countries_found": {"type": "text"},
                    "conservation_status": {"type": "keyword"},
                    "family": {"type": "keyword"},
                    "gestation_period_days": {"type": "keyword"},
                    "top_speed_kmh": {"type": "keyword"},
                    "social_structure": {"type": "text"},
                    "offspring_per_birth": {"type": "keyword"}
                }
            }
        })
        print("Índice animal creado en ElasticSearch")
        return True
    else:
        print("Índice animals ya existe en ElasticSearch")
        return True

def insert_data_elastic(df):
    actions = []
    es = get_connectionElastic()
    for _, row in df.iterrows():
        doc = {
            "_index": "animals",
            "_source": {
                "name": row["Animal"],
                "height_cm": row["Height (cm)"],
                "weight_kg": row["Weight (kg)"],
                "color": row["Color"],
                "lifespan_years": row["Lifespan (years)"],
                "diet": row["Diet"],
                "habitat": row["Habitat"],
                "predators": row["Predators"],
                "average_speed_kmh": row["Average Speed (km/h)"],
                "countries_found": row["Countries Found"],
                "conservation_status": row["Conservation Status"],
                "family": row["Family"],
                "gestation_period_days": row["Gestation Period (days)"],
                "top_speed_kmh": row["Top Speed (km/h)"],
                "social_structure": row["Social Structure"],
                "offspring_per_birth": row["Offspring per Birth"]
            }
        }
        actions.append(doc)

    try:
        helpers.bulk(es, actions)
        print(f"{len(actions)} documentos insertados en ElasticSearch")
        return True
    except Exception as e:
        print(f"Error insertando en ElasticSearch: {e}")
        return False

#-------------------------------------OPEN SEARCH-------------------------------------

def init_opensearch():
    try:
        os_client = OpenSearch(
            hosts=[OPENSEARCH_ENDPOINT],
            http_auth=(OPENSEARCH_USER, OPENSEARCH_PASS),
            use_ssl=True,
            verify_certs=False,   
            ssl_assert_hostname=False,
            ssl_show_warn=False
        )
        if not os_client.ping():
            raise Exception("No se pudo conectar a OpenSearch")
        print("Conexión a OpenSearch exitosa")
        return True
    except Exception as e:
        print(f"Error creando conexión OpenSearch: {e}")
        return False

def upsert_data_opensearch(df):
    os_client = OpenSearch(
            hosts=[OPENSEARCH_ENDPOINT],
            http_auth=(OPENSEARCH_USER, OPENSEARCH_PASS),
            use_ssl=True,
            verify_certs=False,   
            ssl_assert_hostname=False,
            ssl_show_warn=False
    )

    actions = []
    for _, row in df.iterrows():
        doc = {
            "_index": OPENSEARCH_COLLECTION,
            "_source": {
                "name": row["Animal"],
                "height_cm": row["Height (cm)"],
                "weight_kg": row["Weight (kg)"],
                "color": row["Color"],
                "lifespan_years": row["Lifespan (years)"],
                "diet": row["Diet"],
                "habitat": row["Habitat"],
                "predators": row["Predators"],
                "average_speed_kmh": row["Average Speed (km/h)"],
                "countries_found": row["Countries Found"],
                "conservation_status": row["Conservation Status"],
                "family": row["Family"],
                "gestation_period_days": row["Gestation Period (days)"],
                "top_speed_kmh": row["Top Speed (km/h)"],
                "social_structure": row["Social Structure"],
                "offspring_per_birth": row["Offspring per Birth"]
            }
        }
        actions.append(doc)

    try:
        os_helpers.bulk(os_client, actions)
        print(f"{len(actions)} documentos insertados en OpenSearch")
        return True
    except Exception as e:
        print(f"Error insertando en OpenSearch: {e}")
        return False

#-------------------------------------FIN OPEN SEARCH-------------------------------------


#--------------------------------------MONGO DB ------------------------------------------

mongo_client = None

def get_mongo_client():
    global mongo_client
    if mongo_client is None:
        try:
            mongo_client = MongoClient(MONGO_URI)
            # Prueba de conexion
            mongo_client.admin.command("ping")
            print("Conexión a MongoDB exitosa")
        except PyMongoError as e:
            print(f"Error conectando a MongoDB: {e}")
            sys.exit(1)
    return mongo_client


def insert_data_mongo(df):
    """
    Inserta los datos del dataset en una colección 'animals' en MongoDB.
    Un documento por animal, con arrays para habitats y predators.
    """
    try:
        client = get_mongo_client()
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]

        # Opcional: limpiar colección antes de insertar
        collection.delete_many({})
        print(f"Colección {MONGO_COLLECTION} limpiada en MongoDB")

        docs = []
        for _, row in df.iterrows():
            habitats = [h.strip() for h in str(row["Habitat"]).split(",") if h and h.strip() and str(h).lower() != "nan"]
            predators = [p.strip() for p in str(row["Predators"]).split(",") if p and p.strip() and str(p).lower() != "nan"]

            doc = {
                "name": row["Animal"],
                "height_cm": row["Height (cm)"],
                "weight_kg": row["Weight (kg)"],
                "color": row["Color"],
                "lifespan_years": row["Lifespan (years)"],
                "diet": row["Diet"],
                "family": row["Family"],
                "habitats": habitats,
                "predators": predators,
                "average_speed_kmh": row["Average Speed (km/h)"],
                "top_speed_kmh": row["Top Speed (km/h)"],
                "countries_found": row["Countries Found"],
                "conservation_status": row["Conservation Status"],
                "gestation_period_days": row["Gestation Period (days)"],
                "social_structure": row["Social Structure"],
                "offspring_per_birth": row["Offspring per Birth"]
            }

            
            clean_doc = {}

            for k, v in doc.items():
                # Si es lista dejar como está
                if isinstance(v, list):
                    clean_doc[k] = v
                else:
                    # Si es NaN o None poner None, si no, dejar el valor
                    clean_doc[k] = None if pd.isna(v) else v

            docs.append(clean_doc)

        if docs:
            collection.insert_many(docs)
            print(f"{len(docs)} documentos insertados en MongoDB")
        else:
            print("No hay documentos para insertar en MongoDB")

        return True

    except PyMongoError as e:
        print(f"Error insertando datos en MongoDB: {e}")
        return False

#--------------------------------------FIN MONGO DB --------------------------------------

#--------------------------------------COUCH CB ------------------------------------------
def get_couchdb_url():
    return f"http://{COUCHDB_USER}:{COUCHDB_PASS}@{COUCHDB_HOST}:{COUCHDB_PORT}"

def create_database_couchdb():
    url = f"{get_couchdb_url()}/{COUCHDB_DB}"
    try:
        response = requests.put(url, auth=(COUCHDB_USER, COUCHDB_PASS))
        response.raise_for_status()

        if response.status_code == 201:
            print(f"BD creada exitosamente en couch DB")
            return True
        elif response.status_code == 412:
            print(f"BD ya existe en CouchDB, sin problemas.")
            return True
        else:
            print(f"Fallo al crear BD en CouchDB")
            return False

    except requests.exceptions.ConnectionError:
        print("No se puco conectar a CouchDB")
        return False
    except Exception as e:
        print(f"Error inesperado: {e}")
        return False

def insert_data_couchdb(df):
    """
    Inserta los datos del dataset en base de datos animalsdb en CouchBD.
    Crea un documento en la base de datos por documento insertado.
    """
    try:
        url = f"{get_couchdb_url()}/{COUCHDB_DB}"

        docs = []
        for _, row in df.iterrows():
            habitats = [h.strip() for h in str(row["Habitat"]).split(",") if h and h.strip() and str(h).lower() != "nan"]
            predators = [p.strip() for p in str(row["Predators"]).split(",") if p and p.strip() and str(p).lower() != "nan"]

            doc = {
                "name": row["Animal"],
                "height_cm": row["Height (cm)"],
                "weight_kg": row["Weight (kg)"],
                "color": row["Color"],
                "lifespan_years": row["Lifespan (years)"],
                "diet": row["Diet"],
                "family": row["Family"],
                "habitats": habitats,
                "predators": predators,
                "average_speed_kmh": row["Average Speed (km/h)"],
                "top_speed_kmh": row["Top Speed (km/h)"],
                "countries_found": row["Countries Found"],
                "conservation_status": row["Conservation Status"],
                "gestation_period_days": row["Gestation Period (days)"],
                "social_structure": row["Social Structure"],
                "offspring_per_birth": row["Offspring per Birth"]
            }

            
            clean_doc = {}

            for k, v in doc.items():
                # Si es lista dejar como está
                if isinstance(v, list):
                    clean_doc[k] = v
                else:
                    # Si es NaN o None poner None, si no, dejar el valor
                    clean_doc[k] = None if pd.isna(v) else v

            docs.append(clean_doc)

        if docs:
            bulk_response = requests.post(
                    f"{url}/_bulk_docs", 
                    json={"docs": docs},
                    auth=(COUCHDB_USER, COUCHDB_PASS)
                ) #insertado en bulk
            print(bulk_response.json())
            print(f"{len(docs)} documentos insertados en CouchDB")
        else:
            print("No hay documentos para insertar en CouchDB")

        return True

    except Exception as e:
        print(f"Error insertando datos en CouchDB: {e}")
        return False
#--------------------------------------FIN COUCH DB --------------------------------------

#-------------------------------------- NEO4J ------------------------------------------

neo4j_driver = None

def get_neo4j_driver():
    global neo4j_driver
    if neo4j_driver is None:
        uri = f"bolt://{NEO4J_HOST}:{NEO4J_PORT}"
        try:
            neo4j_driver = GraphDatabase.driver(uri, auth=(NEO4J_USER, NEO4J_PASS))
            # prueba de conexión
            with neo4j_driver.session(database=NEO4J_DB) as session:
                session.run("RETURN 1").consume()
            print("Conexión a Neo4j exitosa")
        except Exception as e:
            print(f"Error conectando a Neo4j: {e}")
            sys.exit(1)
    return neo4j_driver


def insert_data_neo4j(df):
    """
    Inserta los datos del dataset en Neo4j con el siguiente modelo:

    (:Animal {name, height_cm, weight_kg, color, lifespan_years, ...})
    (:Diet {name})
    (:Family {name})
    (:Habitat {name})
    (:Predator {name})

    Rel: (Animal)-[:HAS_DIET]->(Diet)
         (Animal)-[:BELONGS_FAMILY]->(Family)
         (Animal)-[:LIVES_IN]->(Habitat)
         (Animal)-[:PREY_OF]->(Predator)
    """
    try:
        driver = get_neo4j_driver()
        with driver.session(database=NEO4J_DB) as session:
            # Opcional: limpiar el grafo antes
            session.run("MATCH (n) DETACH DELETE n").consume()
            print("Grafo limpiado en Neo4j")

            for _, row in df.iterrows():
                animal_name = row["Animal"]
                diet = row["Diet"]
                family = row["Family"]
                habitats = [h.strip() for h in str(row["Habitat"]).split(",") if h and h.strip() and str(h).lower() != "nan"]
                predators = [p.strip() for p in str(row["Predators"]).split(",") if p and p.strip() and str(p).lower() != "nan"]

                params = {
                    "animal_name": animal_name,
                    "height_cm": None if pd.isna(row["Height (cm)"]) else row["Height (cm)"],
                    "weight_kg": None if pd.isna(row["Weight (kg)"]) else row["Weight (kg)"],
                    "color": None if pd.isna(row["Color"]) else row["Color"],
                    "lifespan_years": None if pd.isna(row["Lifespan (years)"]) else row["Lifespan (years)"],
                    "diet": None if pd.isna(diet) else diet,
                    "family": None if pd.isna(family) else family,
                    "avg_speed": None if pd.isna(row["Average Speed (km/h)"]) else row["Average Speed (km/h)"],
                    "top_speed": None if pd.isna(row["Top Speed (km/h)"]) else row["Top Speed (km/h)"],
                    "countries": None if pd.isna(row["Countries Found"]) else row["Countries Found"],
                    "conservation": None if pd.isna(row["Conservation Status"]) else row["Conservation Status"],
                    "gestation": None if pd.isna(row["Gestation Period (days)"]) else row["Gestation Period (days)"],
                    "social": None if pd.isna(row["Social Structure"]) else row["Social Structure"],
                    "offspring": None if pd.isna(row["Offspring per Birth"]) else row["Offspring per Birth"],
                    "habitats": habitats,
                    "predators": predators,
                }

                cypher = """
                MERGE (a:Animal {name: $animal_name})
                ON MATCH SET a.height_cm = $height_cm,
                             a.weight_kg = $weight_kg,
                             a.color = $color,
                             a.lifespan_years = $lifespan_years,
                             a.average_speed_kmh = $avg_speed,
                             a.top_speed_kmh = $top_speed,
                             a.countries_found = $countries,
                             a.conservation_status = $conservation,
                             a.gestation_period_days = $gestation,
                             a.social_structure = $social,
                             a.offspring_per_birth = $offspring
                ON CREATE SET a.height_cm = $height_cm,
                              a.weight_kg = $weight_kg,
                              a.color = $color,
                              a.lifespan_years = $lifespan_years,
                              a.average_speed_kmh = $avg_speed,
                              a.top_speed_kmh = $top_speed,
                              a.countries_found = $countries,
                              a.conservation_status = $conservation,
                              a.gestation_period_days = $gestation,
                              a.social_structure = $social,
                              a.offspring_per_birth = $offspring
                """

                if params["diet"]:
                    cypher += """
                    MERGE (d:Diet {name: $diet})
                    MERGE (a)-[:HAS_DIET]->(d)
                    """

                if params["family"]:
                    cypher += """
                    MERGE (f:Family {name: $family})
                    MERGE (a)-[:BELONGS_FAMILY]->(f)
                    """

                cypher += """
                FOREACH (h IN $habitats |
                    MERGE (hb:Habitat {name: h})
                    MERGE (a)-[:LIVES_IN]->(hb)
                )
                FOREACH (p IN $predators |
                    MERGE (pr:Predator {name: p})
                    MERGE (a)-[:PREY_OF]->(pr)
                )
                """

                session.run(cypher, params).consume()

            print("Datos insertados exitosamente en Neo4j")
            return True

    except Exception as e:
        print(f"Error insertando datos en Neo4j: {e}")
        return False
#---------------------------------------Fin Neo ---------------------------------------------------------------


if __name__ == "__main__":    
    try:
        if MARIADB_ENABLE :
            # Crear base de datos MariaDB si no existe
            conection_mariadb()
        # Ejecutar schema 
        if POSTGRES_ENABLE:
            if not execute_postgress_from_file():
                print("No se pudieron crear las tablas en PostgreSQL")
                sys.exit(1)
        if MARIADB_ENABLE:
            if not execute_MariaDB_from_file():
                print("No se pudieron crear las tablas en MariaDB")
                sys.exit(1)
        if ELASTICSEARCH_ENABLE:
            if not create_index_elastic():
                print("No se pudo crear el índice en ElasticSearch")
                sys.exit(1)

        if OPENSEARCH_ENABLE:
            if not init_opensearch():
                print("No se pudo inicializar OpenSearch")
                sys.exit(1)
                
        if MONGO_ENABLE:
            if not get_mongo_client():
                print("No se pudo inicializar MongoDB")
                sys.exit(1)

        if COUCHDB_ENABLE:
            if not create_database_couchdb():
                print("No se pudo inicializar CouchDB")
                sys.exit(1)
        if NEO4J_ENABLE:
            if not insert_data_neo4j(df):
                print("No se pudo inicializar Neo4j")
                sys.exit(1)

        
        
        
        # Cargar dataset
        df = load_dataset()
        
        # Insertar datos
        if POSTGRES_ENABLE:
            if not insert_data_postgres(df):
                print("No se pudo cargar PostgreSQL")
                sys.exit(1)
        if MARIADB_ENABLE:
            if not insert_data_mariadb(df):
                print("No se pudo cargar MariaDB")
                sys.exit(1)
        if ELASTICSEARCH_ENABLE:
            if not insert_data_elastic(df):
                print("No se pudo cargar ElasticSearch")
                sys.exit(1)

        if OPENSEARCH_ENABLE:
            if not upsert_data_opensearch(df):
                print("No se pudo cargar OpenSearch")
                sys.exit(1)
        
        if MONGO_ENABLE:
            if not insert_data_mongo(df):
                print("No se pudo cargar MongoDB")
                sys.exit(1)

        if COUCHDB_ENABLE:
            if not insert_data_couchdb(df):
                print("No se pudo cargar CouchDB")
                sys.exit(1)



        print("DataSeeder completado exitosamente en todas las bases")
        # if (insert_data_postgres(df) and insert_data_mariadb(df) 
        # and insert_data_elastic(df) and upsert_data_chroma(df) and insert_data_vespa(df)):
        #     print("DataSeeder completado exitosamente en todas las bases")
        # else:
        #     print("Error insertando datos")
        #     sys.exit(1)
            
    except Exception as e:
        print(f"Error general: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("DataSeeder terminado")
