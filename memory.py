from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./memory_db")
collection = client.get_or_create_collection("samantha")

def save_memory(text):
    embedding = model.encode(text).tolist()
    collection.add(
        documents=[text],
        embeddings=[embedding],
        ids=[str(collection.count())]
    )

def search_memory(query, n=3):
    embedding = model.encode(query).tolist()
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n
    )
    return results["documents"][0]