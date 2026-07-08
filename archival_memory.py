from sentence_transformers import SentenceTransformer
import chromadb

# Archival storage (MemGPT sense): curated important facts, written when the LLM itself decides
# something is worth remembering (via tool use), not automatically like recall storage in memory.py.
# (archival storage: recall_memory.py의 recall storage와 달리, LLM이 스스로 "중요하다"고 판단할 때만
# tool use로 기록하는 정제된 사실 저장소)
model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./archival_db")
collection = client.get_or_create_collection("samantha_archival")

def save_archival_memory(text):
    embedding = model.encode(text).tolist()
    collection.add(
        documents=[text],
        embeddings=[embedding],
        ids=[str(collection.count())]
    )

def search_archival_memory(query, n=3):
    if collection.count() == 0:
        return []
    embedding = model.encode(query).tolist()
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n
    )
    return results["documents"][0]
