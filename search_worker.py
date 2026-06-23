# ***********************************************************************
# THIS ISN'T USED ANYMORE, RETRIEVE() FUNCTION HAS BEEN RESOLVED!
# ***********************************************************************
# -----------------------------------------------------------------------
# Search Worker - The Script To Retrieve Chunks From The Database
# A replacement of the retrieve() function in the vector pipeline file
# to deal with segmentation fault issues
# -----------------------------------------------------------------------
# Imported Files Used
import sys
import json
import faiss
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from backend import get_product_by_id
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# Clean Value - Cleans a passed in value to deal with NaN or infinite
# float values that could cause potential issues
# -----------------------------------------------------------------------
def clean_value(v):
    if isinstance(v, float) and (v != v or v == float('inf') or v == float('-inf')):
        return None
    return v
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# Clean Description - Returns a cleaner description text removing text 
# like singlequotes and apostrophes from the CSV format
# -----------------------------------------------------------------------
def clean_description(text):
    # If text is empty
    if not text:
        return ""
    
    # Remove common CSV artifacts
    text = re.sub(r'\bProduct Description\b', '', text)
    text = re.sub(r'Amazon\.com\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bFrom the Manufacturer\b', '', text)
    text = text.strip().strip("'\"[]")
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r"'\s*'", ' ', text)
    text = re.sub(r"'([A-Z])", r' \1', text)

    return text
# -----------------------------------------------------------------------


# -----------------------------------------------------------------------
# Main Function of Search Worker File
# -----------------------------------------------------------------------
# Retrieve the query inputted from the system argument
query = sys.argv[1]
k = int(sys.argv[2])

# Load all chunks from the outputs chunk files
with open("outputs/chunks_docs.json") as f:
    chunks_docs = json.load(f)
with open("outputs/chunks_ids.json") as f:
    chunks_ids = json.load(f)


# Read in the FAISS index and build the model
faiss_index = faiss.read_index("outputs/faiss_index.bin")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Converts the query string to a vector, finds the k most similar vectors
# in the FAISS index, and maps the indices back to their chunk text and
# product ID.
query_vec = np.array(model.encode([query])).astype("float32")
distance, indices = faiss_index.search(query_vec, k)
results = [(chunks_docs[i], chunks_ids[i]) for i in indices[0]]

# Stores the seen product ids and the responses
seen = set()
response = []

# Processing all chunks
for chunk_text, product_id in results:

    # If a product ID was already process, skip it
    if product_id in seen:
        continue

    # Add the product ID in the set of seen
    seen.add(product_id)

    # Retrieve the product by its product ID
    product = get_product_by_id(product_id)

    # If the product exists, add the product to the response
    # Price and average_rating must be cleaned to prevent issues
    if product:
        response.append({
            "product_id": product["product_id"],
            "title": product["title"],
            "description": clean_description(chunk_text[:300]),
            "price": clean_value(product["price"]),
            "average_rating": clean_value(product["average_rating"]),
            "rating_number": product["rating_number"],
            "store": product["store"],
        })

# Printing the response to the terminal
print(json.dumps(response))
# -----------------------------------------------------------------------