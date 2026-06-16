# -----------------------------------------------------------------------
# api.py
# -----------------------------------------------------------------------
# FastAPI layer that exposes the FAISS vector pipeline as HTTP endpoints.
# Builds the FAISS index once on startup, then serves search requests.
# -----------------------------------------------------------------------
# Install dependencies:
#   pip install fastapi uvicorn
# Run:
#   uvicorn api:app --reload
# -----------------------------------------------------------------------
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from backend import load_products_from_db, log_query, get_product_by_id
from vector_pipeline import chunk_documents, embed_chunks, build_index, retrieve

import os

# -----------------------------------------------------------------------
# App Setup
# -----------------------------------------------------------------------
app = FastAPI(title="Amazon Product Semantic Search")

# Allow React frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this down when you deploy
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# Build FAISS index once on startup — stays in memory for all requests
# -----------------------------------------------------------------------
os.makedirs("outputs", exist_ok=True)

print("Loading products from PostgreSQL...")
product_docs, product_ids = [], []
products = load_products_from_db()
for p in products:
    product_docs.append(p["description"])
    product_ids.append(p["product_id"])

print("Chunking and embedding...")
chunks_docs, chunks_ids = chunk_documents(product_docs, product_ids)
embeddings              = embed_chunks(chunks_docs)
faiss_index             = build_index(embeddings)
model                   = SentenceTransformer("all-MiniLM-L6-v2")

print(f"Ready — {len(product_ids)} products indexed.")
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# Request / Response Models
# -----------------------------------------------------------------------
class SearchRequest(BaseModel):
    query: str
    k:     int = 5        # number of results, defaults to 5
    user_id: int = 1      # swap for real auth later
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# POST /search
# Takes a query string, runs FAISS retrieval, logs to DB, returns results
# -----------------------------------------------------------------------
@app.post("/search")
def search(request: SearchRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    results = retrieve(request.query, model, faiss_index, chunks_docs, chunks_ids, request.k)

    # Log to QueryLog
    matched_ids = list({pid for _, pid in results})
    log_query(request.user_id, request.query, matched_ids)

    # Build response — fetch full product details for each matched ID
    seen = set()
    response = []
    for chunk_text, pid in results:
        if pid in seen:
            continue
        seen.add(pid)
        product = get_product_by_id(pid)
        if product:
            response.append({
                "product_id":     product["product_id"],
                "title":          product["title"],
                "description":    chunk_text[:300],
                "price":          product["price"],
                "average_rating": product["average_rating"],
                "rating_number":  product["rating_number"],
                "store":          product["store"],
            })

    return {"query": request.query, "results": response}
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# GET /products/{product_id}
# Returns full details for a single product
# -----------------------------------------------------------------------
@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# GET /health
# Quick check that the API is running
# -----------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "products_indexed": len(product_ids)}
# -----------------------------------------------------------------------
