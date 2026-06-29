import anthropic
import os
from dotenv import load_dotenv
from memory import save_memory, search_memory
from emotion import detect_emotion
from voice import speak
from listen import listen
from persona import build_system_prompt
from relationship import increment_turn
from inference import inference, save_inference, search_inference

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

short_term = []

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

    # 나에 대한 추론 검색
    related_inference = search_inference(user_input)
    inference_context = "\n".join(related_inference)

    # 감정 감지
    emotion = detect_emotion(user_input)
    increment_turn()
    
    # 단기 기억 (최근 6개)
    short_term.append({"role": "user", "content": user_input})
    
    messages = [
        {
            "role": "user",
            "content": f"[관련 기억]\n{memory_context}\n\n[추론 기억]\n{inference_context}"
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

    # 나에 대한 추론을 저장
    # user_input -> 인사이트 반환 -> 인사이트 db 저장 -> db 인사이트 참고하게 유도.
    inference_data = inference(f"나: {user_input}")
    save_inference(inference_data)