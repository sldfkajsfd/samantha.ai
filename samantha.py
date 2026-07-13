import anthropic
import os
import logging
from dotenv import load_dotenv
from recall_memory import search_memory as search_recall_memory
from archival_memory import search_archival_memory, save_archival_memory
from emotion import detect_emotion
from voice import speak
from listen import listen
from persona import build_system_prompt
from relationship import increment_turn
import queue_manager as qm
import working_context as wc

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

logging.basicConfig(
    filename="samantha.log",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    encoding="utf-8"
)
logger = logging.getLogger("samantha")

MEMORY_TOOLS = [
    {
        "name": "search_recall_memory",
        "description": "과거 대화 원문을 검색한다. 지금 대화와 관련 있어 보이는 이전 대화 내용을 찾아야 할 때 호출한다.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "검색할 키워드나 문장"}},
            "required": ["query"]
        }
    },
    {
        "name": "search_archival_memory",
        "description": "이전에 중요하다고 판단해서 저장해둔 사실들을 검색한다.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "검색할 키워드나 문장"}},
            "required": ["query"]
        }
    },
    {
        "name": "save_to_archival_memory",
        "description": "지금 당장 매번 알 필요는 없지만, 나중에 관련 주제가 나오면 참고할 만한 중요한 정보를 저장한다.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "저장할 정보"}},
            "required": ["text"]
        }
    },
    {
        "name": "update_working_context",
        "description": "이름, 선호, 현재 관계 상태처럼 대화 내내 항상 기억하고 있어야 할 핵심적이고 안정적인 사실을 저장하거나 갱신한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "새로 저장할 사실"},
                "replaces": {"type": "string", "description": "이 사실이 기존 사실을 대체하는 경우, 대체되는 기존 사실 (없으면 생략)"}
            },
            "required": ["fact"]
        }
    }
]

MEMORY_GUIDE = """

[기억 도구 사용 안내]
- 이름, 선호, 현재 관계 상태처럼 항상 기억해야 할 안정적인 사실을 알게 되면 update_working_context를 호출해.
- 나중에 참고하면 좋을 세부 정보(예: 과거 특정 사건)는 save_to_archival_memory로 저장해.
- 과거 대화 원문이 필요하면 search_recall_memory를, 저장해둔 중요 사실을 다시 찾아야 하면 search_archival_memory를 사용해.
- 위 도구들은 필요하다고 판단될 때만 사용하고, 매 턴 무조건 사용할 필요는 없어.
- 도구를 쓸 때 "이건 기억해둘게", "저장할게" 같은 말을 하지 마. 도구 호출은 네 생각의 배경 작업일 뿐이야. 유저에게는 항상 지금 대화 흐름에 자연스럽게 이어지는 말만 해.
"""


def handle_queue_status():
    status = qm.check_status()
    logger.info(f"[queue] status={status} total_tokens={qm.total_tokens}")
    if status == "warning":
        qm.insert_warning()
        logger.info("[queue] inserted warning message")
    elif status == "flush":
        qm.flush()
        logger.info(f"[queue] flushed -> total_tokens={qm.total_tokens}")


def execute_tool(name, tool_input):
    logger.info(f"[tool] call name={name} input={tool_input}")
    if name == "search_recall_memory":
        results = search_recall_memory(tool_input["query"])
        result = "\n".join(results) if results else "(검색 결과 없음)"
    elif name == "search_archival_memory":
        results = search_archival_memory(tool_input["query"])
        result = "\n".join(results) if results else "(검색 결과 없음)"
    elif name == "save_to_archival_memory":
        save_archival_memory(tool_input["text"])
        result = "저장 완료"
    elif name == "update_working_context":
        if tool_input.get("replaces"):
            wc.replace_fact(tool_input["replaces"], tool_input["fact"])
        else:
            wc.append_fact(tool_input["fact"])
        result = "working context 갱신 완료"
    else:
        result = "알 수 없는 tool"
    logger.info(f"[tool] result name={name} -> {result!r}")
    return result

# main loop #
if __name__ == "__main__":
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

        # Detect emotion (감정 감지)
        emotion = detect_emotion(user_input)
        increment_turn()

        # Short-term memory via the MemGPT-style queue manager (단기 기억, MemGPT 스타일 큐 매니저)
        qm.add_message("user", user_input)
        handle_queue_status()

        messages = [
            {
                "role": "user",
                "content": f"[핵심 기억 (working context)]\n{wc.get_context_text()}\n\n[이전 대화 요약]\n{qm.recursive_summary}"
            },
            {
                "role": "assistant",
                "content": "알겠어, 참고할게."
            }
        ] + qm.message_queue

        system_prompt = build_system_prompt(emotion) + MEMORY_GUIDE

        logger.info(f"===== turn start ===== user_input={user_input!r} emotion={emotion}")

        # accumulating the replying message from Samantha after functioning tool_use
        all_texts = []
        for i in range(5):
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1024,
                system=system_prompt,
                tools=MEMORY_TOOLS,
                messages=messages
            )

            texts = [block.text for block in response.content if block.type == "text"]
            tool_calls = [(block.name, block.input) for block in response.content if block.type == "tool_use"]
            logger.info(f"[api] iteration={i} stop_reason={response.stop_reason} texts={texts} tool_calls={tool_calls}")

            all_texts.extend(texts)

            if response.stop_reason != "tool_use":
                reply = "\n\n".join(all_texts)
                break

            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            reply = "(도구를 너무 많이 호출해서 답변을 못 만들었어.)"
            logger.info("[api] hit max iterations without a final reply")

        logger.info(f"===== turn end ===== reply={reply!r}")

        # Samantha's reply via TTS (TTS를 이용한 사만다의 반응)
        print(f"사만다: {reply}\n")
        ## add TTS version: speak(reply)

        qm.add_message("assistant", reply)
        handle_queue_status()
