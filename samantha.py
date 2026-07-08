import anthropic
import os
from dotenv import load_dotenv
from memory import search_memory
from emotion import detect_emotion
from voice import speak
from listen import listen
from persona import build_system_prompt
from relationship import increment_turn
from inference import inference, save_inference, search_inference
import queue_manager as qm

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def handle_queue_status():
    status = qm.check_status()
    if status == "warning":
        qm.insert_warning()
    elif status == "flush":
        qm.flush()

while True:
    # Start the conversation via STT (STT를 이용한 대화 시작)
    user_input = input("나: ")
    ## STT version (STT 버전): user_input = listen()
    ##          print(f"나: {user_input}")

    if not user_input or user_input.strip() == "":
        print("(아무 말도 안 들렸어. 다시 시도할게.)")
        continue
    
    if user_input == "종료":
        qm.save_queue_state()
        print("대화 종료.")
        break
    
    # Search long-term memory (장기 기억 검색)
    related_memories = search_memory(user_input)
    memory_context = "\n".join(related_memories)

    # Search inferences about me (나에 대한 추론 검색)
    related_inference = search_inference(user_input)
    inference_context = "\n".join(related_inference)

    # Detect emotion (감정 감지)
    emotion = detect_emotion(user_input)
    increment_turn()

    # Short-term memory via the MemGPT-style queue manager (단기 기억, MemGPT 스타일 큐 매니저)
    qm.add_message("user", user_input)
    handle_queue_status()

    messages = [
        {
            "role": "user",
            "content": f"[관련 기억]\n{memory_context}\n\n[추론 기억]\n{inference_context}\n\n[이전 대화 요약]\n{qm.recursive_summary}"
        },
        {
            "role": "assistant",
            "content": "알겠어, 참고할게."
        }
    ] + qm.message_queue
    
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=build_system_prompt(emotion),
        messages=messages
    )
    
    # Samantha's reply via TTS (TTS를 이용한 사만다의 반응)
    reply = response.content[0].text
    print(f"사만다: {reply}\n")
    ## add TTS version: speak(reply)

    
    qm.add_message("assistant", reply)
    handle_queue_status()

    # Save an inference about me (나에 대한 추론을 저장)
    # user_input -> return insight -> save insight to db -> guide the model to reference the db insight (user_input -> 인사이트 반환 -> 인사이트 db 저장 -> db 인사이트 참고하게 유도)
    inference_data = inference(f"나: {user_input}")
    save_inference(inference_data)