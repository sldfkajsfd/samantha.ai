import anthropic
import os
from dotenv import load_dotenv
from memory import save_memory, search_memory
from emotion import detect_emotion

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

short_term = []

while True:
    user_input = input("나: ")
    
    if user_input == "종료":
        print("대화 종료.")
        break
    
    # 장기 기억 검색
    related_memories = search_memory(user_input)
    memory_context = "\n".join(related_memories)

    # 감정 감지
    emotion = detect_emotion(user_input)
    
    # 단기 기억 (최근 6개)
    short_term.append({"role": "user", "content": user_input})
    
    messages = [
        {
            "role": "user",
            "content": f"[관련 기억]\n{memory_context}"
        },
        {
            "role": "assistant",
            "content": "알겠어, 참고할게."
        }
    ] + short_term
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=f"너는 사만다야. 주어진 관련 기억과 대화 흐름을 참고해서 대화해.\n사용자의 현재 감정 상태: {emotion}\n감정에 맞게 말투를 조절해.",
        messages=messages
    )
    
    reply = response.content[0].text
    print(f"사만다: {reply}\n")
    
    short_term.append({"role": "assistant", "content": reply})
    
    # 단기 기억 최근 6개만 유지
    if len(short_term) > 6:
        short_term = short_term[-6:]
    
    # 장기 기억에 저장
    save_memory(f"나: {user_input}")
    save_memory(f"사만다: {reply}")