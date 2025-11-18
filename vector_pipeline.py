#vector_pipeline.py
#CS 480 Project - Amazon Product Reviews Database - Phase 3) Vector Piepline

#Required Files To Import For Vector Pipelining
#_______________________________________________________________________
#To Load Files And Output To It
import os
import json

#Handling Numeric Arrays For Embeddings
import numpy as np
import pandas as pd

#Adding A Pre-Trained Embedding Model
from sentence_transformers import SentenceTransformer

#Helps Break Long Documents Into Text For Chunking Documents
from langchain_text_splitters import RecursiveCharacterTextSplitter

#The Library FAISS Used For Building The Vector Index
import faiss


#_______________________________________________________________________


#Step 1) Loading Documents
#Process of loading the files and reading them into a document
#_______________________________________________________________________
def load_documents(data_dir="data"):
    docs = []
    csv_path = os.path.join(data_dir, "sample500.csv")
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            for desc in df['description']:
                if isinstance(desc, str) and len(desc.strip()) > 0:
                    docs.append(desc)
            print(f"Loaded {len(docs)} documents from CSV")
        except Exception as e:
            print(f"Error reading CSV")
    else:
        # Fallback to original text file loading
        docs = []
        #Access every file in the folder
        for filename in os.listdir(data_dir):
            #For every TEXT file in the folder ONLY, read the contents of the file
            #and store it inside a doc. Then, add that document to the list of
            #documents
            if filename.endswith('.txt'):
                with open(os.path.join(data_dir, filename), "r", encoding="utf-8") as file:
                    doc = file.read()
                    docs.append(doc)
    return docs
# _______________________________________________________________________
#_______________________________________________________________________


#Step 2) Chunking Documents
#Process of accessing long text in documents and splitting those texts into what is
#known as chunks
#_______________________________________________________________________
def chunk_documents(docs, chunk_size=512, chunk_overlap=50):
    #Initializing a text splitter to split long text into smaller pieces by periods, commas, 
    #or paragraphs cleanly
    #RecursiveCharacterTextSplitters - LangChains Built In Helper To Split Texts Cleanly
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    #Constructing a list of chunks to store informations and return
    chunks = []

    #Access every document and split the document text into a list of strings known as a chunk
    #After successfully retrieving the chunk document, add it to the lists of chunks
    #We use extend to add chunks to merge all texts into one list
    for doc in docs:
        chunk = text_splitter.split_text(doc)
        chunks.extend(chunk)
    
    #Return the list of chunks
    return chunks
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
def retrieve(query, model, index, chunks, k):
    #Convert the query into a high-dimensional vector using the same model we used to convert
    #chunks into high-dimensional vectors
    query_model = model.encode([query])

    #After conversion, find the k most similar models to the query model in the FAISS index
    #where distance represents how similar they are and indices are the rows of those models
    distance, indices = index.search(query_model, k)

    #Lastly, return and retrieved the corresponding models found to be the most similar
    #to that query model
    return [chunks[i] for i in indices[0]]
#_______________________________________________________________________


#Main Code - Vector Pipelining of Amazon Reviews Database
#_______________________________________________________________________
if __name__ == "__main__":
    continueLoop = True
    while continueLoop:
        #Creating an outputs folder first to store the outputs for future use
        os.makedirs("outputs", exist_ok=True)

        #Constructing the SentenceTransformer model to convert the query into
        model = SentenceTransformer("all-MiniLM-L6-v2")

        #Prompt the user to input a query
        query = input("Enter a query: ")
        number = int(input("Total Number of Results: "))

        #__________  Process of Vector Pipelining In Databases ____________
        #      Document → Chunking → Embedding → Indexing → Retrieval
        documents = load_documents()
        chunks = chunk_documents(documents)
        embeddings = embed_chunks(chunks)
        index = build_index(embeddings)
        results = retrieve(query, model, index, chunks, number)
        #___________________________________________________________________

        #Printing the resulting models found to be the most similar to the query
        print("\n--- Most Similar Models Found ---")
        for r in results:
            print(r[:250], "...\n")

        #Search Again?
        choice = input("Do you wish to search again(y/n): ").lower()
        if choice == "y":
            continueLoop = True
        else:
            continueLoop = False
#_______________________________________________________________________