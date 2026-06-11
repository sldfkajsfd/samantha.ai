import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()


client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
HISTORY_FILE = "history.json"

if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        conversation = json.load(f)
else:
    conversation = []

while True:
    user_input = input("나: ")
    
    if user_input == "종료":
        with open(HISTORY_FILE, "w") as f:
            json.dump(conversation, f, ensure_ascii=False, indent=2)
        print("대화가 저장됐어.")
        break
    
    conversation.append({"role": "user", "content": user_input})
    
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        messages=conversation
    )
    
    reply = message.content[0].text
    print(f"사만다: {reply}\n")
    
    conversation.append({"role": "assistant", "content": reply})