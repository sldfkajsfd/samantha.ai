import anthropic
import os
import json
from dotenv import load_dotenv
from recall_memory import save_memory

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

QUEUE_STATE_FILE = "queue_state.json"

## States mimicking MemGPT's main context/queue concept (MemGPT의 main context(큐) 개념을 흉내낸 상태 3가지)

# State 1: FIFO message queue, the recent conversation actually sent to the model (상태 1: FIFO 메시지 큐 - 실제로 모델에 보내는 최근 대화)
message_queue = []
# State 2: recursive summary, compressing the old summary + evicted messages each flush (상태 2: recursive summary - flush될 때마다 이전 요약 + 밀려난 대화를 압축해서 누적)
recursive_summary = ""
# State 3: cumulative token count of message_queue (상태 3: message_queue가 차지하는 누적 토큰 수)
total_tokens = 0

MAX_TOKENS = 4000
WARNING_RATIO = 0.7   # 이 비율 넘으면 경고 메시지 삽입
FLUSH_RATIO = 0.9     # 이 비율 넘으면 flush (evict + 요약 + 원문 저장)


def _estimate_tokens(text: str) -> int:
    # Rough estimate without a real tokenizer, 1 token per 3 characters (별도 토크나이저 없이 쓰는 대략적인 추정치 - 문자 3자당 1토큰)
    return max(1, len(text) // 3)


# Load queue_state.json so the queue/summary survive a restart (재시작해도 큐/요약이 남도록 queue_state.json 읽기)
def load_queue_state():
    global message_queue, recursive_summary, total_tokens
    if os.path.exists(QUEUE_STATE_FILE):
        with open(QUEUE_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        message_queue = data.get("message_queue", [])
        recursive_summary = data.get("recursive_summary", "")
        total_tokens = sum(_estimate_tokens(m["content"]) for m in message_queue)


# Write queue_state.json (queue_state.json 쓰기)
def save_queue_state():
    with open(QUEUE_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"message_queue": message_queue, "recursive_summary": recursive_summary},
            f,
            indent=2,
            ensure_ascii=False
        )


## 1. Add message (메시지 추가)
def add_message(role: str, content: str):
    global total_tokens
    message_queue.append({"role": role, "content": content})
    total_tokens += _estimate_tokens(content)


## 2. Check token ratio -> return normal/warning/flush (토큰 비율 체크 -> normal/warning/flush 리턴)
def check_status(max_tokens: int = MAX_TOKENS) -> str:
    ratio = total_tokens / max_tokens
    if ratio >= FLUSH_RATIO:
        return "flush"
    if ratio >= WARNING_RATIO:
        return "warning"
    return "normal"


## 3. Insert a warning message into the queue on warning (warning 시 큐에 경고 메시지 삽입, MemGPT의 queue warning message)
def insert_warning():
    warning_text = "[시스템 경고] 대화 기억 공간이 얼마 남지 않았어. 곧 오래된 대화가 정리(flush)될 거야."
    add_message("user", warning_text)


## 4. Flush: evict old messages -> update recursive summary -> store raw originals via memory.py (flush: 오래된 메시지 evict -> recursive summary 갱신 -> 원문은 요약 없이 memory.py에 저장)
def flush():
    global message_queue, recursive_summary, total_tokens

    # Reuse FLUSH_RATIO instead of a new constant: keep target after flush = (1 - FLUSH_RATIO) (새 상수 없이 FLUSH_RATIO를 재사용: flush 후 남길 토큰 목표치 = (1 - FLUSH_RATIO))
    keep_target = (1 - FLUSH_RATIO) * MAX_TOKENS

    # Walk backward from the newest message, keeping only what fits under the target (최신 메시지부터 거꾸로 훑으면서 목표 토큰 안에 드는 만큼만 남긴다)
    kept_tokens = 0
    split_index = len(message_queue)
    for i in range(len(message_queue) - 1, -1, -1):
        msg_tokens = _estimate_tokens(message_queue[i]["content"])
        if kept_tokens + msg_tokens > keep_target:
            break
        kept_tokens += msg_tokens
        split_index = i

    if split_index == 0:
        return

    evict_target = message_queue[:split_index]
    remaining = message_queue[split_index:]

    # Core of flush: store the raw original text with no summarization, into long-term memory (archival memory) (flush의 핵심: 요약하지 않고 원문 그대로 장기 기억(archival memory)에 저장)
    for msg in evict_target:
        save_memory(f"{msg['role']}: {msg['content']}")

    # The recursive summary is only a compressed copy for keeping model context, separate from raw storage (recursive summary는 모델 컨텍스트 유지용으로만 압축 생성, 원문 저장과는 별개)
    evict_text = "\n".join(f"{m['role']}: {m['content']}" for m in evict_target)
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        system="다음은 기존 대화 요약과 새로 밀려난 대화 내용이야. 둘을 합쳐서 하나의 누적 요약으로 다시 작성해줘. 핵심 사실과 감정 흐름 위주로 간결하게.",
        messages=[{
            "role": "user",
            "content": f"[기존 요약]\n{recursive_summary or '(없음)'}\n\n[새로 밀려난 대화]\n{evict_text}"
        }]
    )
    recursive_summary = response.content[0].text.strip()

    message_queue = remaining
    total_tokens = sum(_estimate_tokens(m["content"]) for m in message_queue)

    save_queue_state()


# Load saved state on module import (모듈 로드 시 저장된 상태 불러오기)
load_queue_state()
