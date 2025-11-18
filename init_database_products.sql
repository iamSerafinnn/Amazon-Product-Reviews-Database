-- Drop and recreate the database
DROP DATABASE IF EXISTS products_database;
CREATE DATABASE products_database;

-- Connect to the new database
\c products_database;

-- Drop tables if they already exist (in reverse dependency order)
DROP TABLE IF EXISTS QueryLog_Product CASCADE;
DROP TABLE IF EXISTS ProductCategory CASCADE;
DROP TABLE IF EXISTS QueryLog CASCADE;
DROP TABLE IF EXISTS Product CASCADE;
DROP TABLE IF EXISTS Category CASCADE;
DROP TABLE IF EXISTS Curator CASCADE;
DROP TABLE IF EXISTS Admin CASCADE;
DROP TABLE IF EXISTS EndUser CASCADE;
DROP TABLE IF EXISTS Users CASCADE;


-- Parent  table: Users
CREATE TABLE Users (
    user_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);

-- Child table: EndUser
CREATE TABLE EndUser (
    user_id INT PRIMARY KEY,
    last_activity TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

-- Child table: Admin
CREATE TABLE Admin (
    user_id INT PRIMARY KEY,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

-- Child table: Curator
CREATE TABLE Curator (
    user_id INT PRIMARY KEY,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);


-- Category table
CREATE TABLE Category (
    category_id INT PRIMARY KEY,
    title VARCHAR(100) NOT NULL
);

-- Product table
CREATE TABLE Product (
    product_id INT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    type VARCHAR(50),  -- idk why we need this, we can use it as the link to the product or something like that
    source VARCHAR(255),
    added_by INT,
    main_category_id INT,
    store VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    description TEXT,
    price FLOAT,
    images JSONB,          -- URL or JSON array
    average_rating FLOAT,
    rating_number INT,
    features JSONB,        -- JSON array or comma-separated list
    details TEXT,
    FOREIGN KEY (added_by) REFERENCES Users(user_id),
    FOREIGN KEY (main_category_id) REFERENCES Category(category_id)
);
-- we could also implemet categores list json list in the product.
-- Many-to-many association: Product ↔ Category
CREATE TABLE ProductCategory (
    product_id INT,
    category_id INT,
    PRIMARY KEY (product_id, category_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id),
    FOREIGN KEY (category_id) REFERENCES Category(category_id)
);

-- QueryLog table
CREATE TABLE QueryLog (
    query_id INT PRIMARY KEY,
    query_text TEXT NOT NULL,
    user_id INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

-- Association table to store which Products were retrieved by a query
CREATE TABLE QueryLog_Product (
    query_id INT,
    product_id INT,
    PRIMARY KEY (query_id, product_id),
    FOREIGN KEY (query_id) REFERENCES QueryLog(query_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);


CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE ProductEmbeddings (
    embedding_id SERIAL PRIMARY KEY,
    product_id INT UNIQUE REFERENCES Product(product_id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    embedding vector(384) NOT NULL,   -- Because you're using all-MiniLM-L6-v2
    created_at TIMESTAMP DEFAULT NOW()
);


CREATE INDEX idx_product_embeddings_hnsw
ON ProductEmbeddings
USING hnsw (embedding vector_cosine_ops);