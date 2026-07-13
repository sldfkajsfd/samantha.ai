import json
import os
import logging
import anthropic
from dotenv import load_dotenv

# Working context (MemGPT sense): a small set of stable facts (name, preferences, current
# relationship status) that the LLM itself decides to write via tool use. Unlike recall/archival
# storage, this is never searched -- it's always concatenated into every prompt as-is.
# (working context: 이름/선호/현재 관계 상태처럼 LLM이 스스로 판단해서 tool로 써넣는 소수의 안정적
# 사실. recall/archival storage와 달리 검색하지 않고 매번 프롬프트에 그대로 포함됨)

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
logger = logging.getLogger("samantha")

WORKING_CONTEXT_FILE = "working_context.json"

# working_context는 archival_memory와 달리 상한이 없으면 관계가 쌓일수록 매턴 토큰 비용이
# 무한히 늘어나고, 낡은 사실이 안 걸러져 정합성도 깨진다. message_queue/recursive_summary와
# 같은 패턴(임계치 도달 시 압축)을 적용한다.
# (unlike archival_memory, working_context has no eviction, so without a cap it grows every
# turn's token cost forever and lets stale facts pile up. mirror the message_queue/recursive_summary
# pattern: consolidate via LLM once it crosses a threshold)
MAX_TOKENS = 500
CONSOLIDATE_RATIO = 0.9

working_context = []


def _estimate_tokens(text: str) -> int:
    # Rough estimate without a real tokenizer, 1 token per 3 characters (별도 토크나이저 없이 쓰는 대략적인 추정치 - 문자 3자당 1토큰)
    return max(1, len(text) // 3)


def load_working_context():
    global working_context
    if os.path.exists(WORKING_CONTEXT_FILE):
        with open(WORKING_CONTEXT_FILE, "r", encoding="utf-8") as f:
            working_context = json.load(f)


def save_working_context():
    with open(WORKING_CONTEXT_FILE, "w", encoding="utf-8") as f:
        json.dump(working_context, f, indent=2, ensure_ascii=False)


# Ask the LLM to merge/dedupe/drop stale facts into a denser set, same idea as queue_manager.py's
# flush() (재정리: LLM에게 중복/낡은 사실을 합치거나 버리고 더 밀도 높은 소수의 사실로 재작성시킴)
def _consolidate():
    global working_context

    facts_text = "\n".join(f"- {fact}" for fact in working_context)
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        system=(
            "다음은 한 사용자에 대해 누적된 핵심 사실 목록이야. 중복되거나 서로 모순되는 "
            "사실은 최신 내용 기준으로 합치고, 더 이상 유효하지 않은 낡은 사실은 제거해서, "
            "지금도 참인 핵심 사실만 간결한 항목들로 다시 정리해줘. 각 줄은 '- '로 시작하는 "
            "한 문장으로 작성해."
        ),
        messages=[{"role": "user", "content": facts_text}]
    )
    consolidated_text = response.content[0].text.strip()
    working_context = [
        line.lstrip("- ").strip()
        for line in consolidated_text.split("\n")
        if line.strip()
    ]
    save_working_context()
    logger.info(f"[working_context] consolidated -> {len(working_context)} facts")


def _check_and_consolidate():
    total_tokens = sum(_estimate_tokens(fact) for fact in working_context)
    if total_tokens / MAX_TOKENS >= CONSOLIDATE_RATIO:
        _consolidate()


def append_fact(text: str):
    working_context.append(text)
    save_working_context()
    _check_and_consolidate()


def replace_fact(old: str, new: str):
    if old in working_context:
        working_context[working_context.index(old)] = new
    else:
        working_context.append(new)
    save_working_context()
    _check_and_consolidate()


def get_context_text() -> str:
    if not working_context:
        return "(없음)"
    return "\n".join(f"- {fact}" for fact in working_context)


load_working_context()
