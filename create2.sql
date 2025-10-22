-- Parent  table: Users
CREATE TABLE USERS (
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

-- Document table
CREATE TABLE Product (
    document_id INT PRIMARY KEY,
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
-- Many-to-many association: Document ↔ Category
CREATE TABLE DocumentCategory (
    document_id INT,
    category_id INT,
    PRIMARY KEY (document_id, category_id),
    FOREIGN KEY (document_id) REFERENCES Document(document_id),
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

-- Association table to store which documents were retrieved by a query
CREATE TABLE QueryLog_Document (
    query_id INT,
    document_id INT,
    PRIMARY KEY (query_id, document_id),
    FOREIGN KEY (query_id) REFERENCES QueryLog(query_id),
    FOREIGN KEY (document_id) REFERENCES Document(document_id)
);
