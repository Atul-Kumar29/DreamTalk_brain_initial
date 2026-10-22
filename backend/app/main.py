import json
from uuid import uuid4
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.config import settings
from app.database import Base, engine, get_db
from app.models import Conversation, Message
from app.schemas import ChatRequest, ChatResponse, Delivery, Emotion, MessageOut, SessionOut
from app.brain import generate_reply

Base.metadata.create_all(bind=engine)
app = FastAPI(title="DreamTalk Brain API", version="0.1.0", description="MVP conversation brain for DreamTalk")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health():
    provider = "groq" if "groq.com" in settings.openai_base_url.lower() else "openai"
    return {"status": "ok", "provider": provider if settings.openai_api_key else "demo", "model": settings.openai_model if settings.openai_api_key else None}


@app.get("/api/sessions", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db)):
    return db.query(Conversation).order_by(Conversation.created_at.desc()).limit(30).all()


@app.post("/api/sessions", response_model=SessionOut)
def create_session(db: Session = Depends(get_db)):
    session = Conversation(id=str(uuid4()))
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@app.get("/api/sessions/{session_id}/messages", response_model=list[MessageOut])
def get_messages(session_id: str, db: Session = Depends(get_db)):
    session = db.get(Conversation, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return session.messages


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    session = db.get(Conversation, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(session)
    db.commit()
    return {"deleted": True}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    session_id = payload.session_id
    session = db.get(Conversation, session_id) if session_id else None
    if session_id and not session:
        raise HTTPException(status_code=404, detail="Conversation not found. Start a new conversation.")
    if not session:
        session = Conversation(id=str(uuid4()), title=payload.message[:54].strip() or "New conversation")
        db.add(session)
        db.flush()
        session_id = session.id

    history = list(session.messages)
    user_message = Message(conversation_id=session_id, role="user", content=payload.message, emotion="unknown", intent="user_message")
    db.add(user_message)
    db.flush()
    try:
        result, demo_mode = generate_reply(payload.message, history)
    except Exception as exc:
        db.rollback()
        if isinstance(exc, (json.JSONDecodeError, ValueError)):
            raise HTTPException(status_code=502, detail="The model returned an invalid response. Please try again.") from exc
        raise HTTPException(status_code=502, detail="The LLM provider request failed. Check the API key, model name, and provider status.") from exc

    assistant_message = Message(
        conversation_id=session_id,
        role="assistant",
        content=result["reply"],
        emotion=result["emotion"],
        intent=result["intent"],
    )
    db.add(assistant_message)
    db.commit()
    return ChatResponse(
        session_id=session_id,
        reply=result["reply"],
        emotion=Emotion(label=result["emotion"], confidence=result["confidence"]),
        intent=result["intent"],
        delivery=Delivery(style=result["delivery_style"], pace=result["pace"]),
        demo_mode=demo_mode,
    )
