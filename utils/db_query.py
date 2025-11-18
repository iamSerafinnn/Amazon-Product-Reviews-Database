from sqlalchemy import text
import json
import numpy as np

def add_prereq(engine, user_id: int, user_name: str, user_email: str,
               category_id: int, category_title: str):
    """
    Ensure that the prerequisite entries exist for inserting a product:
    - User in Users table
    - Category in Category table
    """
    # Insert user if not exists
    insert_user_query = """
    INSERT INTO Users (user_id, name, email)
    VALUES (:user_id, :name, :email)
    ON CONFLICT (user_id) DO NOTHING;
    """
    run_command(insert_user_query, {"user_id": user_id, "name": user_name, "email": user_email})

    # Insert category if not exists
    insert_category_query = """
    INSERT INTO Category (category_id, title)
    VALUES (:category_id, :title)
    ON CONFLICT (category_id) DO NOTHING;
    """
    run_command(insert_category_query, {"category_id": category_id, "title": category_title})

    print(f"Prerequisites ensured: user {user_id}, category {category_id}")


def insert_product_with_embedding(engine, data, embedding_vector, product_id=1, added_by=1, main_category_id=1):

    if isinstance(embedding_vector, np.ndarray):
        embedding_vector = embedding_vector.tolist()

    product_data = {
        "product_id": product_id,
        "title": data.get("title"),
        "type": None,
        "source": None,
        "added_by": added_by,
        "main_category_id": main_category_id,
        "store": data.get("store"),
        "description": data.get("description"),
        "price": data.get("price") if not np.isnan(data.get("price", 0)) else None,
        "images": json.dumps(data.get("images", {})), 
        "average_rating": data.get("average_rating"),
        "rating_number": data.get("rating_number"),
        "features": json.dumps(data.get("features", {})),
        "details": json.dumps(data.get("details", {}))
    }

    insert_product_query = """
    INSERT INTO Product (
        product_id, title, type, source, added_by, main_category_id, store,
        description, price, images, average_rating, rating_number, features, details
    ) VALUES (
        :product_id, :title, :type, :source, :added_by, :main_category_id, :store,
        :description, :price, :images, :average_rating, :rating_number, :features, :details
    )
    ON CONFLICT (product_id) DO NOTHING;
    """

    insert_embedding_query = """
    INSERT INTO ProductEmbeddings (product_id, description, embedding)
    VALUES (:product_id, :description, :embedding)
    ON CONFLICT (product_id) DO NOTHING;
    """

    with engine.begin() as conn:
        conn.execute(text(insert_product_query), product_data)
        conn.execute(text(insert_embedding_query), {
            "product_id": product_id,
            "description": data.get("description"),
            "embedding": embedding_vector
        })

    print(f"Inserted product {product_id} with embedding.")



def insert_product_with_embedding(engine, data, embedding_vector, product_id=1, added_by=1, main_category_id=1):
    if isinstance(embedding_vector, np.ndarray):
        embedding_vector = embedding_vector.tolist()

    product_data = {
        "product_id": product_id,
        "title": data.get("title"),
        "type": None,
        "source": None,
        "added_by": added_by,
        "main_category_id": main_category_id,
        "store": data.get("store"),
        "description": data.get("description"),
        "price": data.get("price") if not np.isnan(data.get("price", 0)) else None,
        "images": json.dumps(data.get("images", {})), 
        "average_rating": data.get("average_rating"),
        "rating_number": data.get("rating_number"),
        "features": json.dumps(data.get("features", {})),
        "details": json.dumps(data.get("details", {}))
    }

    insert_product_query = """
    INSERT INTO Product (
        product_id, title, type, source, added_by, main_category_id, store,
        description, price, images, average_rating, rating_number, features, details
    )
    VALUES (
        :product_id, :title, :type, :source, :added_by, :main_category_id, :store,
        :description, :price, :images, :average_rating, :rating_number, :features, :details
    )
    ON CONFLICT (product_id) DO NOTHING;
    """

    insert_embedding_query = """
    INSERT INTO ProductEmbeddings (product_id, description, embedding)
    VALUES (:product_id, :description, :embedding)
    ON CONFLICT (product_id) DO NOTHING;
    """

    try:
        with engine.begin() as conn:  # Transaction starts here
            conn.execute(text(insert_product_query), product_data)
            conn.execute(text(insert_embedding_query), {
                "product_id": product_id,
                "description": data.get("description"),
                "embedding": embedding_vector
            })
        print(f"Inserted product {product_id} with embedding.")
    except Exception as e:
        print(f"Failed to insert product {product_id}: {e}")
        # The transaction is automatically rolled back

def search_products(engine, query_embedding, top_k=5):
    if isinstance(query_embedding, np.ndarray):
        query_embedding = query_embedding.tolist()

    # Convert Python list to PostgreSQL array literal
    pg_array = "ARRAY[" + ",".join(map(str, query_embedding)) + "]::vector"

    search_query = f"""
    SELECT product_id
    FROM ProductEmbeddings
    ORDER BY embedding <-> {pg_array}
    LIMIT :top_k;
    """

    with engine.connect() as conn:
        result = conn.execute(
            text(search_query),
            {"top_k": top_k}
        )
        product_ids = [row[0] for row in result]

    return product_ids

def get_product_title(engine, product_id):
    query = """
    SELECT title
    FROM Product
    WHERE product_id = :product_id;
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"product_id": product_id}).fetchone()
        if result:
            return result[0]
        else:
            return None

