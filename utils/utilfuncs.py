from openai import OpenAI


BATCH_EMBEDDING_MAX = 30
EMBEDDING_SIZE = 300
EMBEDDING_MODEL = "text-embedding-3-small"


def batch_embed_openai(client, texts, model=EMBEDDING_MODEL, batch_size=BATCH_EMBEDDING_MAX, embedding_size = EMBEDDING_SIZE):
    embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.embeddings.create(input=batch, dimensions=embedding_size, model=model)
        batch_embeddings = [e.embedding for e in response.data]
        embeddings.extend(batch_embeddings)

    return embeddings
