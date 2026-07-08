import json
import os

# Working context (MemGPT sense): a small set of stable facts (name, preferences, current
# relationship status) that the LLM itself decides to write via tool use. Unlike recall/archival
# storage, this is never searched -- it's always concatenated into every prompt as-is.
# (working context: 이름/선호/현재 관계 상태처럼 LLM이 스스로 판단해서 tool로 써넣는 소수의 안정적
# 사실. recall/archival storage와 달리 검색하지 않고 매번 프롬프트에 그대로 포함됨)

WORKING_CONTEXT_FILE = "working_context.json"

working_context = []


def load_working_context():
    global working_context
    if os.path.exists(WORKING_CONTEXT_FILE):
        with open(WORKING_CONTEXT_FILE, "r", encoding="utf-8") as f:
            working_context = json.load(f)


def save_working_context():
    with open(WORKING_CONTEXT_FILE, "w", encoding="utf-8") as f:
        json.dump(working_context, f, indent=2, ensure_ascii=False)


def append_fact(text: str):
    working_context.append(text)
    save_working_context()


def replace_fact(old: str, new: str):
    if old in working_context:
        working_context[working_context.index(old)] = new
    else:
        working_context.append(new)
    save_working_context()


def get_context_text() -> str:
    if not working_context:
        return "(없음)"
    return "\n".join(f"- {fact}" for fact in working_context)


load_working_context()
