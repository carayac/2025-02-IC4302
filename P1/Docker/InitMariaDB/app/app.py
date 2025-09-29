import os
import mariadb

# MariaDB
MARIADB_HOST = os.getenv('MARIADB')
MARIADB_USER = os.getenv('MARIADB_USER')
MARIADB_PASS = os.getenv('MARIADB_PASS')
MARIADB_DB = os.getenv('MARIADB_DB')
MARIADB_TABLE = os.getenv('MARIADB_TABLE')
MARIADB_TABLE_BOOKS = os.getenv('MARIADB_TABLE_BOOKS')
MARIADB_TABLE_REVIEWS = os.getenv('MARIADB_TABLE_REVIEWS')

def conectar_MariaDB():
    conn = mariadb.connect(
        host= MARIADB_HOST,
        user= MARIADB_USER,
        password= MARIADB_PASS
    )
    cursor = conn.cursor()

    # Crear la base de datos si no existe
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MARIADB_DB}")
    cursor.execute(f"USE {MARIADB_DB}")

    # Crear tabla de objetos procesados
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {os.getenv('MARIADB_TABLE')} (
        id INT AUTO_INCREMENT PRIMARY KEY,   
        key_name VARCHAR(512),
        fecha_proceso DATETIME DEFAULT CURRENT_TIMESTAMP,
        num_documents INT
        procesado BIT
    )
    """)

    # Crear tabla de libros
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {MARIADB_TABLE_BOOKS} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        object_key VARCHAR(512) NOT NULL,
        title VARCHAR(500),
        authors TEXT,
        description TEXT,
        categories TEXT,
        published_date DATE,
        publisher VARCHAR(255),
        preview_link TEXT,
        info_link TEXT,
        image_link TEXT,
        ratings_count INT,
        FOREIGN KEY (object_key) REFERENCES {MARIADB_TABLE}(key_name)
    );
    """)

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {MARIADB_TABLE_REVIEWS} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        object_key VARCHAR(512) NOT NULL,
        book_id INT,
        title VARCHAR(500),
        price DECIMAL(10,2),
        user_id VARCHAR(50),
        profile_name VARCHAR(255),
        review_helpfulness VARCHAR(20),
        review_score FLOAT,
        review_time DATETIME,
        review_summary TEXT,
        review_text TEXT,
        FOREIGN KEY (object_key) REFERENCES {MARIADB_TABLE}(key_name),
        FOREIGN KEY (book_id) REFERENCES {MARIADB_TABLE_BOOKS}(id)
    );
    """)
    conn.commit()
    return conn, cursor