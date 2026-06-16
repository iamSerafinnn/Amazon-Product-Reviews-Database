#Required Files To Import For Vector Pipelining
#_______________________________________________________________________
import os
import json
import numpy as np
import pandas as pd
import faiss.swigfaiss as faiss

from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend import load_products_from_db, log_query
#_______________________________________________________________________


#Step 1) Loading Documents
#Process of loading the files and reading them into a products array
#_______________________________________________________________________
def load_documents(data_dir="data"):

    products = load_products_from_db()
    product_docs, product_ids = [], []

    # Load all the products from the database
    if products:
        for product in products:
            product_docs.append(product["description"])
            product_ids.append(product["product_id"])
        print("Database has been filled!")
        return product_docs, product_ids
    else:
        print("Database returned no rows.")
    

    # Retrieving data directory, the CSV we will be using
    csv_path = os.path.join(data_dir, "sample500.csv")
    
    if os.path.exists(csv_path):
        try:
            # Reading the csv file into a dataframe
            df = pd.read_csv(csv_path)

            # Load all product ids and descriptions
            for id, desc in enumerate(df['description']):
                if isinstance(desc, str) and len(desc.strip()) > 0:
                    product_docs.append(desc)
                    product_ids.append(id)
            
            print(f"Loaded {len(product_docs)} documents from CSV")

        # Error Handling
        except Exception as e:
            print(f"Error reading CSV")
        
    else:
        #Access every file in the folder
        for id, filename in enumerate(os.listdir(data_dir)):
            
            #For every TEXT file in the folder ONLY, read the contents of the file
            #and store it inside a doc. Then, add that document to the list of
            #documents
            if filename.endswith('.txt'):
                with open(os.path.join(data_dir, filename), "r", encoding="utf-8") as file:
                    product_docs.append(file.read())
                    product_ids.append(id)

    return product_docs, product_ids
#_______________________________________________________________________


#Step 2) Chunking Documents
#Process of accessing long text in documents and splitting those texts into what is
#known as chunks
#_______________________________________________________________________
def chunk_documents(docs, ids, chunk_size=512, chunk_overlap=50):
    # Text splitter to split long text into smaller pieces by periods, commas, or paragraphs cleanly
    # RecursiveCharacterTextSplitters - LangChains Built In Helper To Split Texts Cleanly
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # Arrays to store chunks
    chunks_docs = []
    chunks_ids = []

    # Get each chunk and extend them to the chunks lists
    for doc, id in zip(docs, ids):
        chunk = text_splitter.split_text(doc)
        chunks_docs.extend(chunk)
        chunks_ids.extend([id] * len(chunk))
    
    # Return the resulting chunks
    return chunks_docs, chunks_ids
#_______________________________________________________________________


#Step 3) Embedding Chunks
#Process of converting text chunks into high-dimensional vectors of floating_point numerical
#numbers known as embeddings needed for vector databases like FAISS or pgvector to use
#_______________________________________________________________________
def embed_chunks(chunks):
    #Loading SentenceTransformer, a model library that translates sentences into meaningful
    #high-dimentional vectors of floating_point numbers (Model Used = all-MiniLM-L6-v2)
    model = SentenceTransformer("all-MiniLM-L6-v2")

    #Generate the embeddings using the model we constructed that converts our passed in
    #chunks into high-dimensional vectors of numerical numbers
    #Displays the progress as it generates those embeddings
    embeddings = model.encode(chunks, show_progress_bar=True)

    #Then we need to save our embeddings and chunks metadata into the outputs folder
    #for future access or reloading
    #___________________________________________________
    #Embeddings: Save into a numpy binary file (.npy)
    np.save("outputs/embeddings.npy", embeddings)

    #Text Chunks: Save into a json file (.json)
    with open("outputs/chunks.json", "w") as file:
        json.dump(chunks, file)
    #___________________________________________________
    
    #After saving the embeddings and chunks, return the resulting embeddings
    return embeddings
#_______________________________________________________________________


#Step 4) Building FAISS Index
#Process of building the FAISS index, the searchable syestem structure that stores embeddings
#and allows fast searches of similar chunk_text based on a given query
#_______________________________________________________________________
def build_index(embeddings):
    #Get the length of the vector dimension from the 2D numpy array of embeddings where
    #shape[1] stores length of dimension per vector needed for FAISS index
    dimension = embeddings.shape[1]

    #Build the FAISS index using IndexFLatL2 that compares vectors using L2 euclidean distance
    index = faiss.IndexFlatL2(dimension)

    #Then load all your embeddings into the new constructed FAISS index
    index.add(embeddings)

    #For future used, make sure to save the FAISS index into a binary file in the outputs folder
    faiss.write_index(index, "outputs/faiss_index.bin")
    
    #Lastly return the constructed FAISS index
    return index
#_______________________________________________________________________


#Step 5) Retrieving Chunks
#Process of taking in a user query, convert that query into a high-dimensional vector, then use that vector
#to find the most similar high-dimensional vectors in the FAISS index (Retrieval of Chunks In The FAISS Index)
#_______________________________________________________________________
def retrieve(query, model, index, chunks_docs, chunks_ids, k):
    #Convert the query into a high-dimensional vector using the same model we used to convert
    #chunks into high-dimensional vectors
    query_model = model.encode([query])

    #After conversion, find the k most similar models to the query model in the FAISS index
    #where distance represents how similar they are and indices are the rows of those models
    distance, indices = index.search(query_model, k)

    #Lastly, return and retrieved the corresponding models found to be the most similar
    #to that query model
    return [(chunks_docs[i], chunks_ids[i]) for i in indices[0]]
#_______________________________________________________________________


#Main Code - Vector Pipelining of Amazon Reviews Database
#_______________________________________________________________________
if __name__ == "__main__":
    #Creating an outputs folder first to store the outputs for future use
    os.makedirs("outputs", exist_ok=True)

    #Constructing the SentenceTransformer model to convert the query into
    model = SentenceTransformer("all-MiniLM-L6-v2")

    #__________  Process of Vector Pipelining In Databases ____________
    #           Document → Chunking → Embedding → Indexing
    product_docs, product_ids = load_documents()
    chunks_docs, chunks_ids   = chunk_documents(product_docs, product_ids)
    embeddings = embed_chunks(chunks_docs)
    index = build_index(embeddings)
    #___________________________________________________________________

    continueLoop = True
    while continueLoop:
        
        #Prompt the user to input a query
        query = input("Enter a query: ")
        number = int(input("Total Number of Results: "))

        # Retrieving the results
        results = retrieve(query, model, index, chunks_docs, chunks_ids, number)

        # Get all matching product IDs of the results
        matched_ids = list({product_id for _, product_id in results})

        # Insert all the maching product IDs into the database
        log_query(1, query, matched_ids)

        #Printing the resulting models found to be the most similar to the query
        print("\n--- Most Similar Models Found ---")
        for chunk_text, pid in results:
            print(f"[product_id={pid}] {chunk_text[:250]}...\n")

        #Search Again?
        choice = input("Do you wish to search again(y/n): ").lower()
        if choice == "y":
            continueLoop = True
        else:
            "Okay. Bye!"
            continueLoop = False
#_______________________________________________________________________