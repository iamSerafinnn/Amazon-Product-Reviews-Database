import numpy as np
import pandas as pd
from utils.utilfuncs import batch_embed_openai
from utils.LLM import LanguageModelClient
from nltk.tokenize import sent_tokenize
from sklearn.metrics.pairwise import cosine_similarity
import re
import nltk
from nltk.tokenize import word_tokenize
from sqlalchemy import create_engine
from openai import OpenAI
import ssl
import json
import pyarrow as pa

def clean_text(text):
    # Not a text, thus return empty string
    if not isinstance(text, str):
        return ""
    
    # Remove brackets, braces, and quotes
    text = re.sub(r"[\[\]\{\}\'\"]", " ", text)
    
    # Remove backslashes and newlines
    text = re.sub(r"\\[nrt]", " ", text)
    
    # Replace multiple spaces with one
    text = re.sub(r"\s+", " ", text)
    
    # Tokenize and rejoin (to normalize spacing, keep punctuation)
    tokens = word_tokenize(text)
    cleaned = " ".join(tokens)
    return cleaned.strip()

def text_to_paragraph_chunks(text, target_words=100):
    sentences = sent_tokenize(text)
    chunks, current_chunk, word_count = [], [], 0

    for sent in sentences:
        n_words = len(sent.split())
        if word_count + n_words > target_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk, word_count = [], 0
        current_chunk.append(sent)
        word_count += n_words

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def similar_idx(q, space, top_x=1):
    q = np.array(q).reshape(1, -1)            
    space = np.array(space)                   
    sim_scores = cosine_similarity(q, space) 
    top_indices = np.argsort(sim_scores[0])[::-1][:top_x]
    return top_indices.tolist()
