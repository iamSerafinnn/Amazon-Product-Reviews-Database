# -----------------------------------------------------------------------
# api.py - FastAPI
# -----------------------------------------------------------------------
# FastAPI layer that exposes the FAISS vector pipeline as HTTP endpoints.
# Builds the FAISS index once on startup, then serves search requests.
# Initiates communication between the backend and the frontend.
# -----------------------------------------------------------------------
# Install dependencies:
#   pip install fastapi uvicorn
# Run:
#   pkill -f uvicorn
#   uvicorn api:app --reload
# -----------------------------------------------------------------------
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from backend import load_products_from_db, log_query, get_product_by_id
from vector_pipeline import chunk_documents, embed_chunks, build_index, retrieve
import os
import faiss
import json
import numpy as np
import subprocess
import sys
import math
import decimal
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# App Setup
# -----------------------------------------------------------------------
# Setting the FastAPI app 
app = FastAPI(title="Amazon Product Database Semantic Search")

# Allow React frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# Build FAISS index once on startup. Stays in memory for all requests
# -----------------------------------------------------------------------
# Create an output directory and its output files to prevent
# building the FAISS index again for faster processes
os.makedirs("outputs", exist_ok=True)
INDEX_PATH = "outputs/faiss_index.bin"
DOCS_PATH = "outputs/chunks_docs.json"
IDS_PATH = "outputs/chunks_ids.json"

# If the path already exist, the index has already been built
if os.path.exists(INDEX_PATH) and os.path.exists(DOCS_PATH):
    print("Index already built...\nLoading products from disk...")

    # Load the faiss index from the index path file
    faiss_index = faiss.read_index(INDEX_PATH)

    # Load the chunks for the chunks files
    with open(DOCS_PATH) as file:
        chunks_docs = json.load(file)
    with open(IDS_PATH) as file:
        chunks_ids = json.load(file)

    # Loading all the product ids and descriptions
    product_ids = list(set(chunks_ids))
    product_docs = list(set(chunks_docs))

# Else, the index has not been built, and must be built
else:
    print("Index not built...\nLoading products from PostgreSQL...")

    # Arrays to load the product descriptions and ids
    product_docs, product_ids = [], []

    # Loading in all the products
    products = load_products_from_db()

    # Retrieving the product IDs and descriptions
    for p in products:
        product_docs.append(p["description"])
        product_ids.append(p["product_id"])

    print("Chunking and embedding...")

    # Chunking the products
    chunks_docs, chunks_ids = chunk_documents(product_docs, product_ids)

    # Creating the vector embeddings for the chunks
    embeddings = embed_chunks(chunks_docs)

    # Building the FAISS index
    faiss_index = build_index(embeddings)

    # Open json file for the chunks and write them in
    with open(IDS_PATH, "w") as file:
        json.dump(chunks_ids, file)
    with open(DOCS_PATH, "w") as file:
        json.dump(chunks_docs, file)

# Loading SentenceTransformer, a model library that translates sentences into meaningful
# high-dimentional vectors of floating_point numbers (Model Used = all-MiniLM-L6-v2)
model = SentenceTransformer("all-MiniLM-L6-v2")

print(f"Ready — {len(product_ids)} products indexed.")
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# Request / Response Models - Defines what a search request must look like
# -----------------------------------------------------------------------
class SearchRequest(BaseModel):
    query: str
    k: int = 5
    user_id: int = 1
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# POST /search
# Takes a query string, runs FAISS retrieval, logs to DB, returns results
# -----------------------------------------------------------------------
@app.post("/search")
async def search(request: SearchRequest):
    print(f"Search received: {request.query}")

    # The search query cannot be empty
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Search through the index with the input query and retrieve the results.
    # Prevent blocking the main thread and Uvicron, with await run_in_threadpool.
    results = await run_in_threadpool(
        retrieve, request.query, model, faiss_index, chunks_ids, request.k
    )

    # Gets all product ids from results
    matched_ids = list({r["product_id"] for r in results})

    # Logs the search query and all product ids
    log_query(request.user_id, request.query, matched_ids)

    # Return the results and the inputted query
    return {"query": request.query, "results": results}
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# GET /products/{product_id}
# Returns full details for a single product based on the product_id
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
# Quick check that the API is running and how many products were indexed
# -----------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "products_indexed": len(product_ids)}
# -----------------------------------------------------------------------
