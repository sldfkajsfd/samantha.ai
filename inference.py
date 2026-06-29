import anthropic
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb

load_dotenv()

client = anthropic.Anthropic(api_key = os.getenv("ANTHROPIC_API_KEY"))

## 대화에서 사만다가 나에 대한 인사이트 추론
 # anthropic api 호출 후 대답 return하는 과정
def inference(text: str) -> str:
  response = client.messages.create(
    model = "claude-haiku-4-5",
    max_tokens = 150,
    system = "다음 문장을 기반으로 나에 생각과 감정,행동 경향을 추론해서 딱 한 문장으로 요약해줘.",
    messages = [{"role": "user", "content": text}]
  )
  return response.content[0].text.strip().lower()


## ChromaDB 별도 컬렉션에 저장
model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="./inference_db")
collection = chroma_client.get_or_create_collection("samantha_inference")

def save_inference(text):
    ## 텍스트를 숫자 벡터로 변환해주는 임베딩
  embedding = model.encode(text).tolist()
  collection.add(
    ## 원본 텍스트
    documents = [text],
    ## 숫자 벡터
    embeddings = [embedding],
    ## 고유 식별자
     # ids는 chromaDB 규칙 상 str이어야해서 변환하는 것임
    ids = [str(collection.count())]
  )

## 사만다가 추론 부분 참고하는 함수
def search_inference(query, n = 3):
    if collection.count() == 0:
      return []
    else:
    # 현재 대화와 가장 관련된 3개의 문장을 chromaDB에서 골라온다.
      embedding = model.encode(query).tolist()
      results = collection.query(
          query_embeddings=[embedding],
          n_results=n
      )
    # 임베딩되어 있는 숫자들을 다시 문자로 변환한다.
      return results["documents"][0]
