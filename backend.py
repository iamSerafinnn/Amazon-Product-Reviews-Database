# -----------------------------------------------------------------------
# The Backend of Amazon Product Reviews Database System
# -----------------------------------------------------------------------
# Handles PostgreSQL connection and all DB interactions for the FAISS pipeline.
# Two responsibilities:
#   1. Pull product descriptions from the Product table (input to FAISS)
#   2. Log queries and matched products back to QueryLog / QueryLog_Product
# -----------------------------------------------------------------------
# Running Process (Terminal Commands)
# -----------------------------------------------------------------------
# pip install psycopg2-binary
# pip install langchain-text-splitters
# pip install faiss-cpu
# pip install fastapi uvicorn
# source venv/bin/activate
# uvicorn api:app --reload
# psql postgres
# \du
# CREATE ROLE postgres WITH SUPERUSER LOGIN PASSWORD 'password.';
# \q
# psql -U postgres -f create_query.sql
# python3 seed.py
# python3 backend.py
# python3 vector_pipeline.py
# -----------------------------------------------------------------------
import psycopg2
import math, decimal
import os
from psycopg2.extras import RealDictCursor
from datetime import datetime
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# Configuration — PostgreSQL Credentials to execute SQL Queries
# -----------------------------------------------------------------------
DATABASE_URL = "postgresql://postgres:xxxxxxxx@mainline.proxy.rlwy.net:PORT/railway"
DB_CONFIG = {
    "host":     os.environ.get("PGHOST", "mainline.proxy.rlwy.net"),
    "port":     int(os.environ.get("PGPORT", 15026)),
    "dbname":   os.environ.get("PGDATABASE", "railway"),
    "user":     os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD", "gmQKUZTlgvsJFwPtVSkpQmOGndWYsJqt"),
}
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# Get Connection - Connect PostgreSQL Credentials to Pyscopg2 database
# adapter for python.
# -----------------------------------------------------------------------
def get_connection():
    return psycopg2.connect(**DB_CONFIG)
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# Load_Products - Fetches product_id, title, and description from the
# Product table.
# -----------------------------------------------------------------------
def load_products_from_db():
    # Query to be executed
    query = """
        SELECT product_id, title, description
        FROM Product
        WHERE description IS NOT NULL
          AND TRIM(description) <> ''
        ORDER BY product_id;
    """
    # Store products
    products = []
    # Store Pyscopg2 Connection
    conn = None

    try:
        # Get PostgreSQL and Pyscopg2 connection
        conn = get_connection()

        # Connection executes the query, takes all rows, and
        # converts each row into a dictionary. Stores all as
        # an array of dictionaries.
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()
            products = [dict(row) for row in rows]
            # [{"product_id": 1, "title": "...", "description": "..."}, ...]
        
        print(f"Loaded {len(products)} products from PostgreSQL.")

    # Error Handling
    except Exception as e:
        print(f"Error loading products from DB: {e}")

    # Close the connection after the its uses
    finally:
        if conn:
            conn.close()

    # Return the loaded products
    return products
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# Log-Query - Inserting into QueryLog and QueryLog_Product Table after
# every search
#   user_id:             ID of the user running the search (use 1 for testing)
#   query_text:          The raw search string the user typed
#   matched_product_ids: List of product_id ints returned by FAISS retrieve()
# -----------------------------------------------------------------------
def log_query(user_id: int, query_text: str, matched_product_ids: list[int]):
    # Query executed to insert row into QueryLog
    query_QUERYLOG = """
        INSERT INTO QueryLog (query_text, user_id, timestamp)
        VALUES (%s, %s, %s)
        RETURNING query_id;
    """
    # Query executed to link query IDs to product IDs
    query_PRODUCT = """
        INSERT INTO QueryLog_Product (query_id, product_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING;
    """
    # Store Pyscopg2 Connection
    conn = None

    try:
        # Get PostgreSQL and Pyscopg2 connection
        conn = get_connection()

        with conn.cursor() as cur:
            # Execute the command to insert the items into the query log
            cur.execute(query_QUERYLOG,(query_text, user_id, datetime.now()))

            # Get the results of the query execution for use
            query_id = cur.fetchone()[0]

            # Now for each resulting query_id, link them to their
            # corresponding product_ids
            for product_id in matched_product_ids:
                cur.execute(query_PRODUCT,(query_id, product_id))

        # Now commit the results of the query
        conn.commit()

        print(f"Query logged (query_id={query_id}) with {len(matched_product_ids)} matched products.")

    # Error Handling
    except Exception as e:
        print(f"Error logging query to DB: {e}")
        # Because of the error, changes on the database must be undone
        if conn:
            conn.rollback()
    
    # Close the connection after its use
    finally:
        if conn:
            conn.close()
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# Get-Product - Get the corresponding row as a dictionary based on the
# passed in product ID
# -----------------------------------------------------------------------
def get_product_by_id(product_id: int):
    # Store Pyscopg2 Connection
    conn = None
    # Query to fetch row
    query = "SELECT * FROM Product WHERE product_id = %s;"

    try:
        # Get PostgreSQL and Pyscopg2 connection
        conn = get_connection()

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Fetch the query row of the product ID
            cur.execute(query,(product_id,))
            row = cur.fetchone()

            # Return none if no row exists
            if not row:
                return None
            
            # Make a dictionary of cleaned values, no infinite decimals o NaN Values
            cleaned = {}

            # Clean NaN values right here before returning (No infinite or NaN Values)
            for k, v in dict(row).items():
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    cleaned[k] = None
                elif isinstance(v, decimal.Decimal):
                    f = float(v)
                    cleaned[k] = None if (math.isnan(f) or math.isinf(f)) else f
                else:
                    cleaned[k] = v

            # Return the cleaned values
            return cleaned
        
    # Error handling
    except Exception as e:
        print(f"Error fetching product {product_id}: {e}")
        return None

    # Close the connection after its uses.
    finally:
        if conn:
            conn.close()
# -----------------------------------------------------------------------