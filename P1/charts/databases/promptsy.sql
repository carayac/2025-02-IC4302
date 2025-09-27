USE promptsy;

CREATE TABLE IF NOT EXISTS User(
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    lastname VARCHAR(100) NOT NULL,
    description VARCHAR(800) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Prompt(
    id INT AUTO_INCREMENT PRIMARY KEY,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enabled BOOLEAN DEFAULT TRUE,
    id_user INT,
    likes INT DEFAULT 0,
    FOREIGN KEY (id_user) REFERENCES User(id)
);

CREATE TABLE IF NOT EXISTS Liked(
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_user INT, 
    id_prompt INT,
    FOREIGN KEY (id_user) REFERENCES User(id),
    FOREIGN KEY (id_prompt) REFERENCES Prompt(id)
);

CREATE TABLE IF NOT EXISTS Friend(
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_user INT,
    id_friend INT,
    enabled BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (id_user) REFERENCES User(id),
    FOREIGN KEY (id_friend) REFERENCES User(id)
);

CREATE TABLE IF NOT EXISTS Book(
    id INT AUTO_INCREMENT PRIMARY KEY,
    searchTyper Enum('vector_books', 'vector_reviews', 'text_books', 'text_reviews', 'mariadb') NOT NULL,
    title VARCHAR(200) NOT NULL,
    description VARCHAR(2000) NOT NULL,
    image VARCHAR(255),
    previewLink VARCHAR(255),
    publisher VARCHAR(255),
    published_date DATE,
    infolink VARCHAR(255),
    ratings_count FLOAT,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Author(
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    book_id INT,
    enabled BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (book_id) REFERENCES Book(id)
);

CREATE TABLE IF NOT EXISTS Category(
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    book_id INT,
    enabled BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (book_id) REFERENCES Book(id)
);