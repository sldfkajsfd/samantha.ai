from sentence_transformers import SentenceTransformer
import chromadb

# Recall storage (MemGPT sense): raw conversation log, written automatically and unconditionally
# by queue_manager.py's flush() with no LLM judgment involved. For LLM-curated important facts,
# see archival_memory.py instead. (recall storage: queue_manager.py의 flush()가 LLM 판단 없이
# 무조건 자동으로 쓰는 원문 대화 로그. LLM이 판단해서 쓰는 중요 정보는 archival_memory.py 참고)
model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./memory_db")
collection = client.get_or_create_collection("samantha")

def save_memory(text):
    ## Convert text to a numeric vector -> embedding (텍스트를 숫자 벡터로 변환 -> embedding)
    embedding = model.encode(text).tolist()
    collection.add(
        ## Original text (원본 텍스트)
        documents=[text],
        ## Embedding numeric vector (embeddings 숫자 벡터)
        embeddings=[embedding],
        ## Unique id (고유 식별자)
        ids=[str(collection.count())]
    )

def search_memory(query, n=3):
    embedding = model.encode(query).tolist()
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n
    )
    return results["documents"][0]