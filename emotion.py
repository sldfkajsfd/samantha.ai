import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def detect_emotion(text: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=10,
        system="다음 문장의 감정을 딱 한 단어로만 답해. 반드시 이 중에서 골라: joy, sadness, anger, anxiety, neutral",
        messages=[{"role": "user", "content": text}]
    )
    return response.content[0].text.strip().lower()