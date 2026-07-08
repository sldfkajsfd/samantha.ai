# 사만다 (Samantha)

> A personal AI companion inspired by the film _Her_ — built to truly understand you over time.

---

## About

Built by **Ethan Seo (서승현)** as both a functioning AI companion and a structured path toward becoming an AI engineer — working through each architectural decision from first principles.

## Overview

Samantha is a long-term AI companion system built on top of the Anthropic Claude API. Unlike typical chatbots, Samantha is designed to **remember**, **infer**, and **adapt** — developing a deeper understanding of the user through every conversation.

This project is also a deliberate learning vehicle: built phase by phase to develop real AI engineering intuition, not just the ability to connect APIs.

I am still learning, so welcome all of your feedbacks!

---

## Key Features

- **Long-term memory** — Stores and retrieves past conversations using vector search (ChromaDB + sentence-transformers)
- **User inference engine** — Extracts personality insights from conversations and builds a persistent model of the user
- **Emotion detection** — Classifies user emotion per turn and adjusts response tone accordingly
- **Relationship engine** — Tracks conversational depth and evolves Samantha's communication style over time
- **Persona system** — Consistent character with defined traits, values, and speech patterns
- **Voice I/O** — ElevenLabs TTS for natural speech output; OpenAI Whisper for speech-to-text input

---

## System Architecture

```
User Input
    │
    ├── Emotion Detection (Claude Haiku)
    ├── Long-term Memory Retrieval (ChromaDB vector search)
    ├── User Inference Retrieval (ChromaDB — separate collection)
    │
    ▼
Context Assembly
    │   system prompt (persona + emotion + relationship level)
    │   + memory context (top-3 relevant past conversations)
    │   + inference context (top-3 relevant user insights)
    │   + short-term memory (recent 6 turns, FIFO)
    │
    ▼
Claude API (claude-haiku-4-5)
    │
    ▼
Response
    ├── TTS Output (ElevenLabs)
    ├── Save to long-term memory
    └── Extract & save user insight (inference engine)
```

---

## File Structure

```
samantha/
├── samantha.py        — Main conversation loop; assembles context and calls Claude API
├── memory.py          — Long-term memory: save/search past conversations via ChromaDB
├── inference.py       — User inference engine: extract personality insights, save/search via ChromaDB
├── emotion.py         — Emotion detection: classifies user input into joy/sadness/anger/anxiety/neutral
├── persona.py         — Samantha's character definition: traits, speech style, values
├── relationship.py    — Relationship engine: tracks turn count, adjusts communication style
├── voice.py           — TTS output via ElevenLabs API
├── listen.py          — STT input via OpenAI Whisper (local)
├── memory_db/         — ChromaDB persistent storage (long-term memory)
├── inference_db/      — ChromaDB persistent storage (user inference)
├── relationship.json  — Persistent relationship state
└── .env               — API keys (not committed)
```

---

## Tech Stack

| Component  | Technology                               |
| ---------- | ---------------------------------------- |
| LLM        | Anthropic Claude API (claude-haiku-4-5)  |
| Vector DB  | ChromaDB                                 |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| TTS        | ElevenLabs (multilingual v2)             |
| STT        | OpenAI Whisper (local, base model)       |
| Audio      | sounddevice, soundfile                   |
| Language   | Python 3.12                              |

---

## Setup

### 1. Clone & create virtual environment

```bash
git clone <repo-url>
cd samantha
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
```

### 2. Install dependencies

```bash
pip install anthropic chromadb sentence-transformers elevenlabs openai-whisper sounddevice soundfile python-dotenv
```

### 3. Configure API keys

Create a `.env` file:

```
ANTHROPIC_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
```

### 4. Run

```bash
python samantha.py
```

---

## Design Decisions & Known Limitations

This project is under active development. Current architectural gaps identified through research:

### 1. Short-term memory eviction without summarization

**Current**: When `short_term` exceeds 6 messages, older messages are permanently deleted.  
**MemGPT approach**: Evicted messages should be recursively summarized and prepended to the queue — preserving context without bloating the window.

### 2. Python-driven memory saving vs. LLM self-directed saving

**Current**: `save_inference()` is called by Python on every turn, regardless of whether the content is meaningful.  
**MemGPT approach**: The LLM itself should decide when information is worth saving, using function calling (tool use).

### 3. No token-aware queue management

**Current**: Memory eviction is based on message count (n=6), not actual token usage.  
**MemGPT approach**: A queue manager monitors token consumption, issues memory pressure warnings at ~70% capacity, and flushes at ~100% — storing evicted messages in recall storage for later retrieval.

> Reference: _MemGPT: Towards LLMs as Operating Systems_ (Packer et al., 2023) — [arxiv:2310.08560](https://arxiv.org/abs/2310.08560)

---

## Roadmap

| Phase   | Focus                                       | Status         |
| ------- | ------------------------------------------- | -------------- |
| Phase 1 | Python environment, basic conversation loop | ✅ Done        |
| Phase 2 | ChromaDB long-term memory, vector search    | ✅ Done        |
| Phase 3 | Emotion detection, emotion-aware responses  | ✅ Done        |
| Phase 4 | Persona system, relationship engine         | ✅ Done        |
| Phase 5 | Voice & real-time interface                 | ⏸ Deferred     |
| Phase 6 | Learning & adaptation (inference engine)    | 🔄 In progress |
| Phase 7 | Research integration                        | 📅 Planned     |

---

## method for improving Samantha reading paper

1. MemGPT paper
   2. edit information to memory using "Python" functions -> LLM's self-editing memory / function calling
      (대화에서의 나의 정보를 python에서 직접 함수 호출 후 저장 -> LLM이 정보를 판단하고 스스로 함수 호출하여 저장)

   Why I use this:
   What I learned from this:

- Only the conversation is stored when I typed "종료(end)" before turn it off. IF I didn't do it, Samantha will not store our conversation.
- If my sentences got long, the time which Samantha think and respond is too long.

---
