# Movi Frontend

React + Vite interface for the Movi multimodal transport assistant.

---

## 1. What’s Included

| Module | Purpose |
|--------|---------|
| `pages/BusDashboard.jsx` | Replica of the assignment dashboard, displays daily trips |
| `pages/ManageRoute.jsx`  | Route management view with stops/paths |
| `components/MoviChat.jsx` | Chat widget (text, voice, screenshot upload) |
| `services/api.js` | Axios wrapper targeting FastAPI (`http://localhost:8000`) |

MoviChat exposes mic + speaker controls, keeping the UI aligned with backend voice capabilities.

---

## 2. Setup

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173
```

Update `API_BASE_URL` in `src/services/api.js` if the backend runs on a different host or port.

---

## 3. Using MoviChat

1. Click **“Chat with Movi”** (floating button, bottom-right).
2. Choose an input method:
   - **Text** – type a request and send.
   - **Voice** – press the mic, speak, press again to stop (Deepgram STT).
   - **Image** – attach a dashboard screenshot; Movi will inspect it with GPT‑4o.
3. Listen or read the response:
   - ElevenLabs TTS speaks replies (speaker toggle disables audio if needed).
   - All messages remain in the scrollable conversation history.

Movi automatically passes the active page (`currentPage`) so backend tools apply to the correct context.

---

## 4. Key Components

```text
src/
├─ App.jsx
├─ main.jsx
├─ pages/
│  ├─ BusDashboard.jsx     # default landing page
│  └─ ManageRoute.jsx      # second required view
├─ components/
│  └─ MoviChat.jsx         # multimodal chat widget
└─ services/
   └─ api.js               # Axios instance (base URL + JSON headers)
```

Styling uses Tailwind utility classes; icons come from `lucide-react`.

---

## 5. Helpful Notes

- React 19 + Vite provide instant HMR during development.
- Voice playback uses the browser Audio API; no extra bundlers required.
- Errors from the backend (e.g., missing API keys) surface directly in the chat to speed debugging.


