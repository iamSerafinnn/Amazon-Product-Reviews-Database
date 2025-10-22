## Datasets are linked bellow:

Dataset we are using:
https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/blob/main/raw_meta_Electronics/full-00000-of-00010.parquet 

We cleaned the amazon dataset by taking out rows with no price, empty features, empty description, no main category, and removed the last three null columns. the cleaned dataset is linked bellow:
https://drive.google.com/file/d/15sY1xVYFIWQgI9gmd1HVHm9DU3wsrv9b/view?usp=drive_link 

## Running the dataset init:
1. to start the postgres services: brew services start postgresql
2. to run the sql init: psql -U ali -d postgres -f init_database_products.sql

## Goals:
We aim to create a retrieval-augmented framework to extract similar electronic products based on a given query. We are modeling a category of amazon products in a relatinal database.