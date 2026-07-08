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

- **Long-term memory** — Recall storage (raw conversation log) + archival storage (curated facts), both ChromaDB + sentence-transformers, searched via LLM-directed tool use
- **Working context** — A small, always-in-prompt set of stable facts (name, preferences, and other important information) the LLM writes to itself when it judges something worth remembering
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
    │
    ▼
Context Assembly
    │   system prompt (persona + emotion + relationship level + memory tool guide)
    │   + working context (stable facts: name, preferences, and other important information — always included)
    │   + recursive summary (compressed history from past flushes)
    │   + short-term memory (queue_manager.py: token-aware FIFO queue)
    │
    ▼
Claude API (claude-haiku-4-5) ── tool use loop ──┐
    │                                             │
    │   search_recall_memory / search_archival_memory / save_to_archival_memory / update_working_context
    │                                             │
    ◄─────────────────────────────────────────────┘
    ▼
Response
    ├── TTS Output (ElevenLabs)
    └── Queue manager: warn at 70% tokens, flush at 90% (evict + save raw to recall storage)
```

---

## File Structure

```
samantha/
├── samantha.py        — Main conversation loop; assembles context and calls Claude API
├── queue_manager.py   — MemGPT-style short-term memory: token-aware FIFO queue, recursive summary, flush-to-memory
├── recall_memory.py   — Recall storage: raw conversation log, auto-saved by queue_manager.py's flush(), searched via LLM tool use
├── archival_memory.py — Archival storage: curated important facts, written/searched via LLM tool use
├── working_context.py — Working context: stable facts (name, preferences, and other important information), always in-prompt, written via LLM tool use
├── emotion.py         — Emotion detection: classifies user input into joy/sadness/anger/anxiety/neutral
├── persona.py         — Samantha's character definition: traits, speech style, values
├── relationship.py    — Relationship engine: tracks turn count, adjusts communication style
├── voice.py           — TTS output via ElevenLabs API
├── listen.py          — STT input via OpenAI Whisper (local)
├── memory_db/         — ChromaDB persistent storage (recall storage)
├── archival_db/       — ChromaDB persistent storage (archival storage)
├── relationship.json  — Persistent relationship state
├── queue_state.json   — Persistent short-term queue/summary state (survives restart)
├── working_context.json — Persistent working context state (survives restart)
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

### 1. Short-term memory eviction without summarization — ✅ Resolved

**Bottleneck**: Evicted messages were gone for good — no way to recover the context they held.
**Was**: When `short_term` exceeded 6 messages, older messages were permanently deleted.
**Now**: `queue_manager.py` evicts old messages but recursively summarizes them into `recursive_summary` first, so rough context survives even after eviction.

### 2. No token-aware queue management — ✅ Resolved

**Bottleneck**: A fixed message count doesn't track actual context usage, so eviction could trigger too early (short messages) or too late (long messages).
**Was**: Memory eviction was based on message count (n=6), not actual token usage.
**Now**: `queue_manager.py` tracks token usage, issues a memory-pressure warning at 70% capacity, and flushes at 90% — evicting only enough old messages to fit a token budget, not a fixed count.

### 3. Python-driven memory saving vs. LLM self-directed saving — ✅ Resolved

**Bottleneck**: Samantha's memory was split across 3 structures instead of MemGPT's clean design, and every memory write/read was Python-automatic — `inference.py` generated a "user insight" every single turn regardless of relevance, `memory.py` conflated recall storage and archival storage in one file, there was no working context at all, and even recall storage's search ran unconditionally every turn rather than being triggered by the LLM's own judgment.
**Was**: `inference.py` forced an insight per turn; `memory.py` auto-wrote and auto-searched a single blended storage; no working context existed.
**Now**: `inference.py` deleted. `recall_memory.py` (recall storage) and `archival_memory.py` (archival storage) are separate modules, and `working_context.py` holds stable facts (name, preferences, and other important information) that stay in every prompt. All reading/writing of recall storage, archival storage, and working context is unified behind Claude tool use (`search_recall_memory`, `search_archival_memory`, `save_to_archival_memory`, `update_working_context`) in `samantha.py` — the LLM itself decides when to call each one, matching MemGPT's self-directed memory editing (Section 2.3).

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
| Phase 6 | Learning & adaptation (memory split + working context) | ✅ Done |
| Phase 7 | Research integration                        | 📅 Planned     |

---
