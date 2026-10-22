# DreamTalk MVP

A minimal, full-stack conversational Brain prototype with a Next.js App Router frontend, FastAPI backend, LangChain with Groq hosted inference through its OpenAI-compatible API, and SQLite persistence. It runs in demo mode without an API key, so you can verify the full UI/API/database flow before connecting a provider.

## Requirements

- Node.js 20.9+ (Node 22 LTS recommended)
- Python 3.11 or 3.12 recommended
- An API key for live LLM replies (optional for demo mode)

## 1. Start the backend

Open a terminal:

```bash
cd backend
python -m venv .venv
```

Activate the environment:

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies and create your environment file:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy `.env.example` to `.env`. On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY` in `backend/.env` to your Groq API key. The variable keeps its original name because the backend uses LangChain’s OpenAI-compatible client, but `OPENAI_BASE_URL` points it to Groq. The default model is `openai/gpt-oss-120b`; use a model currently available to your Groq account. If the key is empty, the app uses a small rule-based demo response so you can test the interface without spending API credits. Do not put the API key in the frontend.

Run the backend from the `backend` directory:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/health` and API docs at `http://127.0.0.1:8000/docs`.

## 2. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
```

Copy `.env.local.example` to `.env.local`:

Windows PowerShell:

```powershell
Copy-Item .env.local.example .env.local
```

macOS/Linux:

```bash
cp .env.local.example .env.local
```

Start Next.js:

```bash
npm run dev
```

Open `http://localhost:3000`.

## Features

- Minimal responsive chat UI
- New conversations and recent conversation list
- SQLite persistence for messages and sessions
- Last 12 stored messages included as LLM context
- Structured response metadata for emotion, intent, delivery style, and pace
- Demo mode when no provider key is configured
- Delete conversation
- API health check and interactive OpenAPI docs

## API routes

- `GET /health`
- `GET /api/sessions`
- `POST /api/sessions`
- `GET /api/sessions/{session_id}/messages`
- `DELETE /api/sessions/{session_id}`
- `POST /api/chat` with `{ "message": "...", "session_id": null }`

## Important MVP limits

- SQLite is used to keep local setup simple; migrate to PostgreSQL before multi-user deployment.
- There is no authentication, user isolation, streaming, or rate limiting yet. Do not deploy this as a public service without adding them.
- The emotion label is an approximate model-generated signal, not a measurement of a person's actual emotional state.
- The MVP stores chat text locally in `backend/dreamtalk.db`. Treat it as sensitive data.
- API keys belong only in `backend/.env`, never in the frontend or committed source.
- Google Fonts are loaded remotely by the stylesheet; the app still functions if they are blocked, using fallback fonts.

## Troubleshooting

- If port 8000 is occupied, run Uvicorn with another port and update `NEXT_PUBLIC_API_URL` in `frontend/.env.local`.
- If the browser says the backend is offline, check that Uvicorn is running and the frontend API URL is correct.
- If live calls fail, check the Groq API key, model availability, quota/rate limits, and network connection. Confirm `OPENAI_BASE_URL=https://api.groq.com/openai/v1` is set in `backend/.env`.
- If a dependency install fails, use Python 3.11/3.12 and Node 22 LTS, delete the backend `.venv` or frontend `node_modules`, and reinstall from the provided requirements/package file.
