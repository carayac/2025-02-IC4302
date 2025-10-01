-- Crear la base de datos si no existe
CREATE DATABASE IF NOT EXISTS control;
USE control;

-- Tabla de objetos procesados
CREATE TABLE IF NOT EXISTS objects (
    id INT AUTO_INCREMENT PRIMARY KEY,   
    key_name VARCHAR(512) NOT NULL,
    fecha_proceso DATETIME DEFAULT CURRENT_TIMESTAMP,
    num_documents INT,
    procesado BIT DEFAULT 0
);

-- Tabla de libros
CREATE TABLE IF NOT EXISTS books (
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
    CONSTRAINT fk_books_object FOREIGN KEY (object_key) REFERENCES objects(key_name)
);

-- Tabla de reseñas
CREATE TABLE IF NOT EXISTS reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    object_key VARCHAR(512) NOT NULL,
    book_id INT NOT NULL,
    title VARCHAR(500),
    price DECIMAL(10,2),
    user_id VARCHAR(50),
    profile_name VARCHAR(255),
    review_helpfulness VARCHAR(20),
    review_score FLOAT,
    review_time DATETIME,
    review_summary TEXT,
    review_text TEXT,
    CONSTRAINT fk_reviews_object FOREIGN KEY (object_key) REFERENCES objects(key_name),
    CONSTRAINT fk_reviews_book FOREIGN KEY (book_id) REFERENCES books(id)
);




