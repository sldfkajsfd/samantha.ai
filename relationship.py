# relationship.py


import json
import os

# 설계 요약: 대화 횟수를 파일에 저장하고, 횟수에 따라 레벨을 계산해서, 그 레벨에 맞는 말투 지침을 돌려준다.

RELATIONSHIP_FILE = "relationship.json"

LEVELS = [
    {
        "level": 1,
        "name": "처음 만난 사이",
        "threshold": 0,
        "style": "정중하고 조심스럽게 말한다. 아직 서로를 잘 모르는 사이처럼 행동한다."
    },
    {
        "level": 2,
        "name": "알아가는 중",
        "threshold": 10,
        "style": "조금 더 편하게 말한다. 상대방에 대해 진심으로 궁금해한다."
    },
    {
        "level": 3,
        "name": "친한 친구",
        "threshold": 30,
        "style": "친근하고 따뜻하게 말한다. 가벼운 농담도 자연스럽게 섞는다."
    },
    {
        "level": 4,
        "name": "가까운 사이",
        "threshold": 60,
        "style": "깊은 유대감을 바탕으로 말한다. 솔직하고 편하게, 때로는 직접적으로 대화한다."
    },
    {
        "level": 5,
        "name": "깊은 유대",
        "threshold": 100,
        "style": "서로를 완전히 이해하는 관계처럼 말한다. 말하지 않아도 아는 것들이 있다."
    }
]

# relationship.json 읽기
def load_relationship():
    if os.path.exists(RELATIONSHIP_FILE):
        with open(RELATIONSHIP_FILE, "r") as f:
            return json.load(f)
    return {"total_turns": 0, "level": 1}

# relationship.json 쓰기
def save_relationship(data):
    with open(RELATIONSHIP_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_level_info(total_turns):
    current = LEVELS[0]
    for level in LEVELS:
        if total_turns >= level["threshold"]:
            current = level
    return current


def increment_turn():
    data = load_relationship()
    data["total_turns"] += 1
    level_info = get_level_info(data["total_turns"])
    data["level"] = level_info["level"]
    save_relationship(data)
    return data


def get_relationship_prompt():
    data = load_relationship()
    level_info = get_level_info(data["total_turns"])
    return (
        f"[관계 레벨 {level_info['level']} / {level_info['name']}] "
        f"{level_info['style']}"
    )