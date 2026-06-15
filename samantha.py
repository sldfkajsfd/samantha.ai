import anthropic
import os
from dotenv import load_dotenv
from memory import save_memory, search_memory
from emotion import detect_emotion
from voice import speak
from listen import listen
from persona import get_persona_prompt

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

short_term = []

def build_system_prompt(emotion: str) -> str:
    persona = get_persona_prompt()
    emotion_instruction = f"\n\n## 현재 사용자 감정 상태\n감지된 감정: {emotion}\n이 감정에 맞게 말투와 톤을 조절해."
    return persona + emotion_instruction

while True:
    # STT를 이용한 대화 시작
    user_input = input("나: ")
    ## STT 버전: user_input = listen()
    ##          print(f"나: {user_input}")

    if not user_input or user_input.strip() == "":
        print("(아무 말도 안 들렸어. 다시 시도할게.)")
        continue
    
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
        system=build_system_prompt(emotion),
        messages=messages
    )
    
    # TTS를 이용한 사만다의 반응
    reply = response.content[0].text
    print(f"사만다: {reply}\n")
    speak(reply)

    
    short_term.append({"role": "assistant", "content": reply})
    
    # 단기 기억 최근 6개만 유지
    if len(short_term) > 6:
        short_term = short_term[-6:]
    
    # 장기 기억에 저장
    save_memory(f"나: {user_input}")
    save_memory(f"사만다: {reply}")