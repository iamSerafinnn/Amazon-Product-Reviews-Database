# -----------------------------------------------------------------------
# seed.py
# -----------------------------------------------------------------------
# A one time data-loading script
# Reads sample500.csv and loads rows into the Product and Category tables.
# Run once before faiss.py to populate the database.
# -----------------------------------------------------------------------
# Files needed
# -----------------------------------------------------------------------
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# DB_CONFIG must match backend.py DB_CONFIG exactly
# -----------------------------------------------------------------------
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "products_database",
    "user":     "postgres",
    "password": "password.",
}
# -----------------------------------------------------------------------
# This is the CSV file data we are using
# -----------------------------------------------------------------------
CSV_PATH = "data/sample500.csv"
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# Opening the PostgreSQL connection
# -----------------------------------------------------------------------
def get_connection():
    return psycopg2.connect(**DB_CONFIG)
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# Cleaning the CSV dataset, filtering out empty cells and NaN. Instead of
# null cells, it returns a fallback making products with titles to untitled
# cells instead of null empty ones.
# -----------------------------------------------------------------------
def clean(value, fallback=None):
    # If the value is NaN or empty, return fallback 
    if pd.isna(value) or str(value).strip() == "":
        return fallback
    # Else return the stripped string instead
    return str(value).strip()
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# fetch_category() - Inserts a row's main category into the category table
# and returns the category ID of the table. Also prevents duplicated ones.
# -----------------------------------------------------------------------
def fetch_category(cur, row, inserted_categories):
    # Query to insert into category table
    query_CATEGORY = """
        INSERT INTO Category (title)
        VALUES (%s)
        ON CONFLICT DO NOTHING
        RETURNING category_id;
    """

    # Cleaning the row and then inserting its main_category into the category table
    category_name = clean(row.get("main_category"), fallback="Uncategorized")
    cur.execute(query_CATEGORY,(category_name,))

    # Retrieving the results and fetches the category_id
    result = cur.fetchone()
    if result:
        inserted_categories += 1
        return result["category_id"], inserted_categories
    
    # If the result already exists, fetch the existing id
    else:
        cur.execute(
            "SELECT category_id FROM Category WHERE title = %s;",
            (category_name,)
        )
        return cur.fetchone()["category_id"], inserted_categories
# -----------------------------------------------------------------------



# -----------------------------------------------------------------------
# fetch_category() - Inserts a row's product attributes into the product
# table in the database. Also prevents duplicated ones.
# -----------------------------------------------------------------------
def insert_product(cur, inserted_products, title, description, price, average_rating, rating_number,
                   store, details, features, images, category_id,):
    
    # Query to insert the product
    query_insert = """
        INSERT INTO Product (
            title, description, price, average_rating, rating_number,
            store, details, features, images,
            main_category_id, processed
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
        ON CONFLICT DO NOTHING;
    """

    # Executing the query with the pass in attributes
    cur.execute(query_insert, 
                (
                title, description, price, average_rating, rating_number,
                store, details, features, images,
                category_id
                ))
    
    # Updating the inserted products
    inserted_products += 1
    return inserted_products
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# Seed() - The main function that runs this entire script called in the
# main function
# -----------------------------------------------------------------------
def seed():

    # Checking if the CSV_PATH we are using exist or not.
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found at {CSV_PATH}")
        return
    
    # Reading the CSV file
    df = pd.read_csv(CSV_PATH)
    print(f"Read {len(df)} rows from {CSV_PATH}")

    # Initiate the PostgreSQL Connection
    conn = get_connection()

    # Tracking inserted and skipped items
    inserted_products  = 0
    skipped_products   = 0
    inserted_categories = 0

    try:
        # Using the PostgreSQL connection
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            # Accessing each row in the dataframe
            for idx, row in df.iterrows():

                # Fetching the category ID
                category_id, inserted_categories = fetch_category(cur, row, inserted_categories)

                # Retrieves the row's product attributes
                title          = clean(row.get("title"), fallback="Untitled")
                description = clean(row.get("description")) or clean(row.get("title"))
                price          = row.get("price")
                average_rating = row.get("average_rating")
                rating_number  = row.get("rating_number")
                store          = clean(row.get("store"))
                details        = clean(row.get("details"))
                features       = clean(row.get("features"))
                images         = clean(row.get("images"))

                # Skip rows with no description and title, no title and description
                # implies useless empty data
                if not description:
                    skipped_products += 1
                    continue

                # Converting the product's price and ratings to numeric
                try:
                    price = float(price) if price and str(price).strip() != "" else None
                except (ValueError, TypeError):
                    price = None
                try:
                    average_rating = float(average_rating) if average_rating else None
                except (ValueError, TypeError):
                    average_rating = None
                try:
                    rating_number = int(float(rating_number)) if rating_number else None
                except (ValueError, TypeError):
                    rating_number = None


                # Inserting the product into the product table
                inserted_products = insert_product(cur, inserted_products, title, description, price, average_rating, rating_number, store, details, features, images, category_id)

        # Commit the connection after loading all data
        conn.commit()

        # Feedback on how many were skipped and inserted
        print(f"Done. Inserted {inserted_products} products, "
              f"skipped {skipped_products} (no description and title), "
              f"{inserted_categories} new categories created.")

    # Error handling
    except Exception as e:
        conn.rollback()
        print(f"Error during seeding: {e}")

    # Close the connection after using it
    finally:
        conn.close()
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# main() - Just calling the seed() function
# -----------------------------------------------------------------------
if __name__ == "__main__":
    seed()
# -----------------------------------------------------------------------
