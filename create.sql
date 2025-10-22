-- Fall 2025, CS 480: Database Systems
-- Group Project: Amazon Product Reviews Database
-- Group Members: Serafin Gargantiel, Bryce Sadelski, and Ali Elahi
-- Phase 2: PostgreSQL Relational Schema (schema.sql)
-- Additions To Improve Efficiency
-- _____________________________________________________________
-- Adding this so that when run, the system checks if the database
-- has already been created or not. If created, drop it and create
-- a new one
DROP SCHEMA IF EXISTS uni CASCADE;
CREATE SCHEMA uni;
-- Setting the new schema into the uni CASCADE
SET search_path = uni;
-- _____________________________________________________________
-- Strong Entities {Product, Store, User, Query, Category}
-- The main independent entities in the database
-- _____________________________________________________________
CREATE Table Store (
    storeID SERIAL PRIMARY KEY, -- Simple
    storeName VARCHAR(50) NOT NULL, -- Simple
    storeLocation VARCHAR(30) NOT NULL, -- Simple
    website TEXT -- Simple
);
CREATE Table Product (
    parentAsin VARCHAR(10) PRIMARY KEY, -- Simple
    storeID INT REFERENCES Store(storeID), -- Simple
    title VARCHAR(100) NOT NULL, -- Simple
    price NUMERIC(8,2) NOT NULL, -- Simple
    author VARCHAR (50) NOT NULL, -- Simple
    subtitle TEXT, -- Simple
    details TEXT, -- Simple
    rating_number BIGINT NOT NULL, -- Simple
    average_rating DOUBLE PRECISION NOT NULL -- Simple
);
CREATE Table Category (
    categoryID SERIAL PRIMARY KEY, -- Simple
    categoryName VARCHAR(50) NOT NULL, -- Simple
    description TEXT NOT NULL -- Simple
);
CREATE Table Feature (
    featureID SERIAL PRIMARY KEY, -- Simple
    parentAsin VARCHAR(10) NOT NULL REFERENCES Product(parentAsin), -- Simple
    features TEXT -- Composite
);
CREATE Table UserAccount (
    userID SERIAL PRIMARY KEY, -- Simple
    username VARCHAR(25) NOT NULL UNIQUE, -- Simple
    userPassword VARCHAR(25) NOT NULL, -- Simple
    userEmail VARCHAR(50), -- Simple
    nameOfUser VARCHAR(50), -- Simple
    role TEXT NOT NULL CHECK (role IN ('admin','curator','enduser')) DEFAULT 'enduser',
    last_activity TIMESTAMP
);
CREATE Table Description (
    descriptionID SERIAL PRIMARY KEY, -- Simple
    parentAsin VARCHAR(10) NOT NULL REFERENCES Product(parentAsin), -- Simple
    descriptions TEXT -- Composite
);
CREATE Table Video (
    videoID SERIAL PRIMARY KEY, -- Simple
    parentAsin VARCHAR(10) NOT NULL REFERENCES Product(parentAsin), -- Simple
    uploaderID INT NOT NULL REFERENCES UserAccount(userID), -- Simple
    title TEXT, -- Simple
    video_url TEXT -- Simple
);
CREATE Table Image (
    imageID SERIAL PRIMARY KEY, -- Simple
    parentAsin VARCHAR(10) NOT NULL REFERENCES Product(parentAsin), -- Simple
    uploaderID INT NOT NULL REFERENCES UserAccount(userID), -- Simple
    high_resolution_url TEXT, -- Simple
    large_image_url TEXT, -- Simple
    thumbnail_url TEXT, -- Simple
    variant_type VARCHAR(10) -- Simple
);
-- Associative Weak Entities {Product Category}
-- _____________________________________________________________
CREATE Table ProductCategory (
    -- Connects the strong entities: Product <--> Category
    parentAsin VARCHAR(10) NOT NULL REFERENCES Product(parentAsin), -- Simple
    categoryID INT NOT NULL REFERENCES Category(categoryID) -- Simple
);
-- _____________________________________________________________
-- _____________________________________________________________
CREATE TABLE Document (
    documentID SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    source TEXT,
    added_by INT NOT NULL REFERENCES UserAccount(userID),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE QueryLog (
    queryID SERIAL PRIMARY KEY, -- Simple
    userID INT NOT NULL REFERENCES UserAccount(userID), -- Simple
    queryText TEXT NOT NULL, -- Simple
    queryDate TIMESTAMP NOT NULL, -- Simple
    parentAsin VARCHAR(10) REFERENCES Product(parentAsin), -- Simple
    result TEXT NOT NULL, -- Simple
    documentID INT NOT NULL REFERENCES Document(documentID)
);
CREATE TABLE QueryResult (
    queryID INT NOT NULL REFERENCES QueryLog(queryID),
    documentID INT NOT NULL REFERENCES Document(documentID),
    PRIMARY KEY (queryID, documentID)
);

