import numpy as np
import pandas as pd
import re
import nltk
import ssl
import json
from sqlalchemy import create_engine, text
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize import sent_tokenize, word_tokenize
import pyarrow as pa
from utils.utilfuncs import batch_embed_openai
from utils.LLM import LanguageModelClient
from utils.text import clean_text, text_to_paragraph_chunks, similar_idx
from utils.db_query import add_prereq, insert_product_with_embedding, get_product_title, search_products

# Database configuration
DB_USER = 'postgres'           # your current macOS user / postgres role
DB_PASSWORD = 'password'          # empty if no password
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'products_database'

#Our OpenAI Key, personal password for programmatic access to GPT models.
OPENAI_KEY = "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"

class ProductAnsweringSystem:
    def __init__(self):
        self.engine = None
        self.client = None
        self.gpt41mini = None
        self.current_user = None
        self.df = None
        
    def init(self):
        self.setup_environment()
        self.setup_database()
        self.setup_openAI()
        self.setup_user_tables()
        self.setup_product_tables()
    
    def setup_environment(self):
        try:
            pa.unregister_extension_type("pandas.period")
        except KeyError:
            pass

        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
    
    def setup_database(self):
        self.engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}", pool_pre_ping=True)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT current_database();"))
                print("Connected OK")
        except Exception as e:
            print("Connection failed:", e)
            raise

    def setup_product_tables(self):
        our_tables = [
            """
            CREATE TABLE IF NOT EXISTS product (
                product_id INT PRIMARY KEY,
                title TEXT,
                type TEXT,
                source TEXT,
                added_by INT,
                main_category_id INT,
                store TEXT,
                description TEXT,
                price NUMERIC,
                images JSONB,
                average_rating NUMERIC,
                rating_number INT,
                features JSONB,
                details JSONB
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS productembeddings (
                product_id INT PRIMARY KEY REFERENCES product(product_id),
                description TEXT,
                embedding DOUBLE PRECISION[]
            );
            """
        ]

        with self.engine.connect() as conn:
            for sql in our_tables:
                conn.execute(text(sql))
            conn.commit()

        print("Product and embedding tables created.")

    
    def setup_openAI(self):
        self.client = OpenAI(api_key=OPENAI_KEY)
        self.gpt41mini = LanguageModelClient(model_name="gpt-4.1-mini", api_key=OPENAI_KEY)
        print("OpenAi created.")
    
    def setup_user_tables(self):
        our_tables = [
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'enduser',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id),
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                logout_time TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS query_logs (
                log_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id),
                query_text TEXT NOT NULL,
                response_text TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]
        
        with self.engine.connect() as conn:
            for table_sql in our_tables:
                conn.execute(text(table_sql))
            conn.commit()
        print("User tables created.")

    def register_user(self, username, email, password, role='enduser'):
        check_query = text("SELECT user_id FROM users WHERE username = :username OR email = :email")
        
        with self.engine.connect() as conn:
            user_exists = conn.execute(check_query, {'username': username, 'email': email}).fetchone()
            
            if user_exists:
                print("User already exists.")
                return False
            
            insert_query = text("""
            INSERT INTO users (username, email, password, role) 
            VALUES (:username, :email, :password, :role)
            RETURNING user_id
            """)
            
            result = conn.execute(insert_query, {
                'username': username,
                'email': email,
                'password': password,
                'role': role
            })
            user_id = result.scalar()
            conn.commit()
            
            print(f"User '{username}' registered successfully with ID: {user_id}")
            return user_id
    
    def login_user(self, username, password):
        user_query = text("SELECT user_id, username, password, role FROM users WHERE username = :username")
        
        with self.engine.connect() as conn:
            result = conn.execute(user_query, {'username': username})
            user = result.mappings().fetchone()
            
            if not user:
                print("User not found.")
                return None
            
            if user['password'] == password:
                session_query = text("""
                INSERT INTO user_sessions (user_id) 
                VALUES (:user_id)
                RETURNING session_id
                """)
                
                result = conn.execute(session_query, {'user_id': user['user_id']})
                session_id = result.scalar()
                conn.commit()
                
                self.current_user = {
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'role': user['role'],
                    'session_id': session_id
                }
                
                print(f"User '{username}' logged in successfully.")
                return self.current_user
            else:
                print("Invalid password.")
                return None

    
    def logout_user(self):
        if self.current_user:
            update_query = text("""
            UPDATE user_sessions 
            SET logout_time = CURRENT_TIMESTAMP, is_active = FALSE 
            WHERE session_id = :session_id
            """)
            
            with self.engine.connect() as conn:
                conn.execute(update_query, {'session_id': self.current_user['session_id']})
                conn.commit()
            
            print(f"User '{self.current_user['username']}' logged out.")
            self.current_user = None
        else:
            print("No user is currently logged in")
    
    def search_products(self, query, top_k=5):   
        if not self.current_user:
            print("Please login first to search products")
            return []
        
        try:
            query_embedding = batch_embed_openai(
                self.client,
                [query],
                embedding_size=384
            )[0]
            
            products_found = search_products(self.engine, query_embedding, top_k=top_k)
            self.log_query(query, str(products_found))
            
            return products_found
        except Exception as e:
            print(f"Search failed: {e}")
            return []

    def embed_and_insert(self, max_products=50, added_by_user_id=1, main_category_id=1):
        if self.df is None:
            try:
                self.df = pd.read_csv("./data/sample500.csv")
                print(f"Loaded CSV with {len(self.df)} rows.")
            except Exception as e:
                print(f"Could not load ./data/sample500.csv: {e}")
                return
        
        total_rows = len(self.df)
        if total_rows == 0:
            print("DataFrame is empty, cannot insert products.")
            return

        with self.engine.connect() as conn:
            existing = conn.execute(
                text("SELECT COUNT(*) FROM productembeddings")
            ).scalar() or 0

        offset = existing

        if offset >= total_rows:
            print(f"All {total_rows} products from CSV have already been inserted.")
            return

        end_index = min(offset + max_products, total_rows)
        df_subset = self.df.iloc[offset:end_index]

        print(f"Inserting products {offset + 1} to {end_index} (out of {total_rows}).")
        product_id = offset + 1

        if "description" not in df_subset.columns:
            print("CSV has no 'description' column, can not embed.")
            return

        batch_size = 25

        for start in range(0, len(df_subset), batch_size):
            batch_df = df_subset.iloc[start:start + batch_size]
            batch_descriptions = [
                (desc if len(desc) < 5000 else desc[:5000])
                for desc in batch_df["description"].fillna("").tolist()
            ]

            embeddings = batch_embed_openai(
                self.client,
                batch_descriptions,
                embedding_size=384
            )

            for (idx, row), embedding_vector in zip(batch_df.iterrows(), embeddings):
                data = {
                    "title": row.get("title", ""),
                    "store": row.get("store", ""),
                    "description": row.get("description", ""),
                    "price": row.get("price", None),
                    "images": row.get("images", {}),
                    "average_rating": row.get("average_rating", None),
                    "rating_number": row.get("rating_number", None),
                    "features": row.get("features", {}),
                    "details": row.get("details", {}),
                }

                insert_product_with_embedding(
                    self.engine,
                    data,
                    embedding_vector,
                    product_id=product_id,
                    added_by=added_by_user_id,
                    main_category_id=main_category_id
                )
                product_id += 1

        print(f"Finished inserting up to product_id {product_id - 1}.")

    def list_my_products(self, limit=20):
        if not self.current_user:
            print("You must be logged in.")
            return []

        user_id = self.current_user["user_id"]

        query = text("""
            SELECT product_id, title
            FROM product
            WHERE added_by = :user_id
            ORDER BY product_id
            LIMIT :limit;
        """)

        with self.engine.connect() as conn:
            rows = conn.execute(query, {"user_id": user_id, "limit": limit}).fetchall()

        if not rows:
            print("You have not uploaded any products yet.")
            return []

        print("\nYour uploaded products:")
        for pid, title in rows:
            print(f"  - ID {pid}: {title}")

        return rows
    
    def log_query(self, query_text, response_text):
        if not self.current_user:
            return
        
        insert_query = text("""
        INSERT INTO query_logs (user_id, query_text, response_text) 
        VALUES (:user_id, :query_text, :response_text)
        """)
        
        with self.engine.connect() as conn:
            conn.execute(insert_query, {
                'user_id': self.current_user['user_id'],
                'query_text': query_text,
                'response_text': response_text
            })
            conn.commit()

    def delete_my_product(self, product_id: int):
        if not self.current_user:
            print("You must be logged in.")
            return

        user_id = self.current_user["user_id"]

        with self.engine.begin() as conn:
            own_or_exist = conn.execute(
                text("""
                    SELECT product_id
                    FROM product
                    WHERE product_id = :pid AND added_by = :uid
                """),
                {"pid": product_id, "uid": user_id}
            ).fetchone()

            if not own_or_exist:
                print("You either do not own this product, or it does not exist.")
                return

            conn.execute(
                text("DELETE FROM productembeddings WHERE product_id = :pid"),
                {"pid": product_id}
            )

            result = conn.execute(
                text("DELETE FROM product WHERE product_id = :pid AND added_by = :uid"),
                {"pid": product_id, "uid": user_id}
            )

            if result.rowcount == 0:
                print("Failed to delete product.")
                return

        print(f"Product {product_id} deleted successfully.")

    def admin_update_user(self):
        if not self.current_user or self.current_user["role"] != "admin":
            print("Only admins can update users.")
            return

        user_id = input("Enter the username of the user to edit: ").strip()
        if not user_id:
            print("No username entered.")
            return

        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT user_id, username, email, password, role
                    FROM users
                    WHERE username = :username
                """),
                {"username": user_id}
            )
            user = result.mappings().fetchone()

        if not user:
            print("User not found.")
            return

        print(f"\nEditing user: {user['username']} (id={user['user_id']}, role={user['role']})")
        new_username = input(f"New username [{user['username']}]: ").strip() or user['username']
        new_email    = input(f"New email [{user['email']}]: ").strip() or user['email']
        new_password = input("New password [leave blank to keep unchanged]: ").strip()
        new_role     = input(f"New role (enduser/curator/admin) [{user['role']}]: ").strip() or user['role']

        if new_role not in ["enduser", "curator", "admin"]:
            print("Invalid role. No changes applied.")
            return

        if not new_password:
            new_password = user["password"]

        with self.engine.connect() as conn:
            conn.execute(
                text("""
                    UPDATE users
                    SET username = :username,
                        email = :email,
                        password = :password,
                        role = :role
                    WHERE user_id = :user_id
                """),
                {
                    "username": new_username,
                    "email": new_email,
                    "password": new_password,
                    "role": new_role,
                    "user_id": user["user_id"]
                }
            )
            conn.commit()

        print("User updated successfully.")

    def admin_delete_user(self):
        if not self.current_user or self.current_user["role"] != "admin":
            print("Only admins can delete users.")
            return

        user_id = input("Enter the username of the user to delete: ").strip()
        if not user_id:
            print("No username entered.")
            return

        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT user_id, username, role
                    FROM users
                    WHERE username = :username
                """),
                {"username": user_id}
            )
            user = result.mappings().fetchone()

        if not user:
            print("User not found.")
            return

        if user["user_id"] == self.current_user["user_id"]:
            print("You cannot delete yourself.")
            return

        uid = user["user_id"]
        with self.engine.begin() as conn:
            conn.execute(
                text("""
                    DELETE FROM productembeddings
                    WHERE product_id IN (
                        SELECT product_id
                        FROM product
                        WHERE added_by = :uid
                    )
                """),
                {"uid": uid}
            )
            conn.execute(
                text("DELETE FROM product WHERE added_by = :uid"),
                {"uid": uid}
            )
            conn.execute(
                text("DELETE FROM query_logs WHERE user_id = :uid"),
                {"uid": uid}
            )
            conn.execute(
                text("DELETE FROM user_sessions WHERE user_id = :uid"),
                {"uid": uid}
            )
            conn.execute(
                text("DELETE FROM users WHERE user_id = :uid"),
                {"uid": uid}
            )

        print(f"User '{user['username']}' and all related data have been deleted.")



    def get_all_users(self):
        if not self.current_user or self.current_user['role'] != 'admin':
            print("Access denied: Admin privileges required.")
            return []
        
        users_query = text("SELECT user_id, username, email, role, created_at FROM users ORDER BY user_id")
        with self.engine.connect() as conn:
            result = conn.execute(users_query)
            users = result.mappings().all()
            return [dict(row) for row in users]

    
    def get_query_logs(self, user_id=None):
        if not self.current_user or self.current_user['role'] != 'admin':
            print("Access denied: Admin privileges required.")
            return []
        
        if user_id:
            logs_query = text("SELECT * FROM query_logs WHERE user_id = :user_id ORDER BY timestamp DESC")
            params = {'user_id': user_id}
        else:
            logs_query = text("SELECT * FROM query_logs ORDER BY timestamp DESC")
            params = {}
        
        with self.engine.connect() as conn:
            result = conn.execute(logs_query, params)
            logs = result.mappings().all()
            return [dict(row) for row in logs]

    def handle_registration(self):
        print("\nUSER REGISTRATION")
        username = input("Username: ").strip()
        email = input("Email: ").strip()
        password = input("Password: ").strip()
        role = input("Role (enduser/curator/admin), default = enduser: ").strip() or 'enduser'
        
        if role not in ['enduser', 'curator', 'admin']:
            print("Invalid role. Must be: enduser, curator, or admin")
            return
        
        self.register_user(username, email, password, role)
    
    def handle_login(self):
        print("\nUSER LOGIN")
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        
        self.login_user(username, password)
    
    def handle_search(self):
        if not self.current_user:
            print(" Please login first")
            return
        
        print("\nPRODUCT SEARCH")
        query = input("Enter your search query: ").strip()
        
        try:
            top_k = int(input("Number of results, 5 is default: ").strip() or "5")
        except ValueError:
            top_k = 5
        
        results = self.search_products(query, top_k)
        
        if results:
            print(f"\n Found {len(results)} results:")
            for i, product_id in enumerate(results, 1):
                title = get_product_title(self.engine, product_id)
                print(f"{i}. {title}")
        else:
            print(" No results found")

    
    def handle_admin(self):
        if not self.current_user or self.current_user['role'] not in ['admin', 'curator']:
            print("Admin/curator access required")
            return
        
        role = self.current_user['role']
        is_admin = (role == 'admin')
        is_curator = (role == 'curator')
        
        while True:
            print("\nADMIN AND CURATOR PANEL")
            print("1. View all users (admin only)")
            print("2. View query logs (admin only)")
            print("3. Insert products from CSV (curator only)")
            print("4. List my uploaded products (curator only)")
            print("5. Delete one of my products (curator only)")
            print("6. Edit a user (admin only)")
            print("7. Delete a user (admin only)")
            print("8. Back to main menu\n")

            
            choice = input("Select option: ").strip()
            
            if choice == '1':
                if not is_admin:
                    print("Only admins can view all users.")
                else:
                    users = self.get_all_users()
                    print(f"\nTotal users: {len(users)}")
                    for user in users:
                        print(f"  - {user['username']} ({user['role']}) - {user['email']}")
            elif choice == '2':
                if not is_admin:
                    print("Only admins can view query logs.")
                else:
                    user_id = input("User ID (leave empty for all): ").strip()
                    if user_id:
                        try:
                            user_id = int(user_id)
                        except ValueError:
                            print("Invalid user ID")
                            continue
                    
                    logs = self.get_query_logs(user_id if user_id else None)
                    print(f"\nQuery logs: {len(logs)} entries")
                    for log in logs[:10]:
                        print(f"  - User {log['user_id']}: {log['query_text'][:50]}...")
            elif choice == '3':
                if not is_curator:
                    print("Only curators can insert products from CSV.")
                else:
                    try:
                        max_products_str = input("How many products to insert from CSV? Default = 50: ").strip()
                        max_products = int(max_products_str) if max_products_str else 50
                    except ValueError:
                        max_products = 50
                    
                    self.embed_and_insert(max_products=max_products, added_by_user_id=self.current_user["user_id"])
            elif choice == '4':
                if not is_curator:
                    print("Only curators can list their products.")
                else:
                    self.list_my_products(limit=20)
            elif choice == '5':
                if not is_curator:
                    print("Only curators can delete their products.")
                else:
                    pid_str = input("Enter the product ID to delete: ").strip()
                    try:
                        pid = int(pid_str)
                    except ValueError:
                        print("Invalid product ID.")
                        continue
                    self.delete_my_product(pid)
            elif choice == '6':
                if not is_admin:
                    print("Only admins can edit users.")
                else:
                    self.admin_update_user()

            elif choice == '7':
                if not is_admin:
                    print("Only admins can delete users.")
                else:
                    self.admin_delete_user()
            elif choice == '8':
                break
            else:
                print("Invalid choice.")


    def run_program(self):        
        while True:
            print(f"\nWelcome{' ' + self.current_user['username'] + ' (' + self.current_user['role'] + ')' if self.current_user else ''}.")
            print("\nOptions:")
            print("1. Register new user")
            print("2. Login")
            print("3. Search products")
            print("4. Admin/Curator functions")
            print("5. Logout" if self.current_user else "5. Exit")
            print("6. Exit")
            
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == '1':
                self.handle_registration()
            elif choice == '2':
                self.handle_login()
            elif choice == '3':
                self.handle_search()
            elif choice == '4':
                self.handle_admin()
            elif choice == '5':
                if self.current_user:
                    self.logout_user()
                else:
                    print("Goodbye!")
                    break
            elif choice == '6':
                if self.current_user:
                    self.logout_user()
                print("Goodbye!")
                break
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    system = ProductAnsweringSystem()
    system.init()
    system.run_program()