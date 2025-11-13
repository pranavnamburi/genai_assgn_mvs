# Movi – Multimodal Transport Agent

**Multimodal assistant for MoveInSync transport ops**  
FastAPI • LangGraph • React • SQLite • Deepgram • ElevenLabs • GPT‑4o 

---

## 1. Overview

Movi understands **text, voice, and screenshots** to support the full Stop → Path → Route → Trip workflow.  
The current build demonstrates:

- ✅ Full-stack web app (React + FastAPI + SQLite) seeded with realistic transport data  
- ✅ LangGraph agent with **16 tools**, consequence-awareness, and confirmation flow  
- ✅ GPT‑4o for screenshot understanding (trip selection, highlights, etc.)  
- ✅ Deepgram speech-to-text and ElevenLabs text-to-speech for voice interaction



---

## 2. Environment Setup

### 2.1 Prerequisites

| Runtime | Reason |
|---------|--------|
| Python 3.12+ | Required for FastAPI, LangGraph, SQLAlchemy |
| Node.js 18+  | Required for Vite/React dev server |
| npm          | Frontend dependency manager |

### 2.2 Backend

```bash
cd backend
pip install -r requirements.txt
python3 seed.py          # Populates SQLite with demo data
```

Configure `.env` (required for audio + vision):
```
OPENAI_API_KEY=...
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...
```

Run the API:
```bash
python3 main.py          # http://localhost:8000
```

### 2.3 Frontend

```bash
cd frontend
npm install
npm run dev              # http://localhost:5173
```

> ℹ️ Voice replies are optional—disable the speaker icon in chat if API keys are not provided.

---

## 3. Features at a Glance

| Area | Highlights | Why it matters |
|------|------------|----------------|
| **Backend API** | FastAPI, CORS, REST endpoints (`/api/{stops,paths,routes,vehicles,drivers,trips}`) | Powers UI with live data |
| **LangGraph Agent** | 16 tools (read/create/update/delete), tribal knowledge consequence flow, confirmation prompts | Mirrors assignment spec for high-risk ops |
| **Multimodal Input** | File upload pipeline → GPT‑4o prompt | Allows “remove the vehicle from this trip” with annotated screenshots |
| **Audio I/O** | Deepgram STT, ElevenLabs TTS, microphone & playback controls | Fully voice-enabled demo flow |
| **Frontend UI** | BusDashboard + ManageRoute pages, MoviChat with context awareness | Matches assignment screenshots |
| **Database Layer** | SQLite seeded with 14 stops, 5 paths, 8 routes, 10 vehicles, 10 drivers, 8 daily trips | Realistic data for all tools |

---

## 4. How to Demo

1. **Launch** both servers.
2. Visit `http://localhost:5173`.
3. Open Movi chat (bottom-right).
4. Try these flows:
   - **Text**: “What’s the status of Bulk - 00:01?”  
   - **Voice**: Click mic → say “List unassigned vehicles” → send.  
   - **Image**: Upload dashboard screenshot with arrow → say “Remove the vehicle from this trip.”  
   - **High-risk**: “Deactivate route Path-1 - 07:00” → observe warning → reply “yes”.

All responses are formatted for speech (no markdown artifacts, spaced license plates, etc.).

---

## 5. Architecture Summary

```
React (Vite)
  ├─ BusDashboard.jsx / ManageRoute.jsx
  └─ MoviChat.jsx
        ├─ Axios → /api/chat
        ├─ Deepgram STT (mic button)
        └─ ElevenLabs TTS (speaker toggle)

FastAPI (main.py)
  ├─ /api/chat        → invokes LangGraph agent
  ├─ /api/speech-to-text → Deepgram REST
  ├─ /api/text-to-speech → ElevenLabs REST
  └─ /api/stops...etc → data feeds

LangGraph (agent.py)
  ├─ State: messages, currentPage, confirmation flags, image bytes
  ├─ Nodes: call_model → check_consequences → handle_confirmation → call_tool
  └─ Tools: 16 total (read/create/update/delete, plus vision-aware helpers)

SQLite (movi_transport.db)
  └─ Seeded via seed.py (stops, paths, routes, vehicles, drivers, trips, deployments)
```
---

## 7. Useful Documentation

- [backend/AGENT_README.md](backend/AGENT_README.md) – in-depth agent & tool reference   


---

## 8. Troubleshooting Quick Reference

| Issue | Fix |
|-------|-----|
| Backend 8000 in use | kill -9 $(lsof -ti:8000)  |
| Frontend 5173 in use | kill -9 $(lsof -ti:5173) |
| Missing deps | Backend: `pip install -r backend/requirements.txt` • Frontend: `npm install` |
| STT/TTS silent | Ensure `.env` contains valid Deepgram/ElevenLabs keys |
| DB mismatch | `cd backend && python3 seed.py` |

---


