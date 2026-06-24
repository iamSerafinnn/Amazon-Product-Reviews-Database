cat > create_tables.sql << 'EOF'
CREATE TABLE IF NOT EXISTS Users (user_id INT PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(100) UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS EndUser (user_id INT PRIMARY KEY, last_activity TIMESTAMP, FOREIGN KEY (user_id) REFERENCES Users(user_id));
CREATE TABLE IF NOT EXISTS Admin (user_id INT PRIMARY KEY, FOREIGN KEY (user_id) REFERENCES Users(user_id));
CREATE TABLE IF NOT EXISTS Curator (user_id INT PRIMARY KEY, FOREIGN KEY (user_id) REFERENCES Users(user_id));
CREATE TABLE IF NOT EXISTS Category (category_id INT PRIMARY KEY, title VARCHAR(100) NOT NULL);
CREATE TABLE IF NOT EXISTS Product (product_id INT PRIMARY KEY, title VARCHAR(255) NOT NULL, type VARCHAR(50), source VARCHAR(255), added_by INT, main_category_id INT, store VARCHAR(255), timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, processed BOOLEAN DEFAULT FALSE, description TEXT, price FLOAT, images TEXT, average_rating FLOAT, rating_number INT, features TEXT, details TEXT, FOREIGN KEY (main_category_id) REFERENCES Category(category_id));
CREATE TABLE IF NOT EXISTS QueryLog (query_id SERIAL PRIMARY KEY, query_text TEXT NOT NULL, user_id INT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS QueryLog_Product (query_id INT, product_id INT, PRIMARY KEY (query_id, product_id), FOREIGN KEY (query_id) REFERENCES QueryLog(query_id), FOREIGN KEY (product_id) REFERENCES Product(product_id));
EOF