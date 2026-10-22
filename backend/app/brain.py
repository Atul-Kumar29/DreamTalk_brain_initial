import json
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.models import Message

SYSTEM_PROMPT = """You are DreamTalk, a thoughtful AI companion. Be warm, natural, grounded, and concise. Do not claim to be human or to know the user's feelings with certainty. Treat emotion labels as estimates. Never invent memories. Use relevant conversation context. Return only valid JSON with keys: reply (string), emotion (one of empathetic, calm, curious, encouraging, joyful, neutral), confidence (number 0 to 1), intent (short snake_case string), delivery_style (one of calm, warm, curious, upbeat, direct), pace (one of gentle, normal, brisk)."""


def demo_reply(message: str) -> dict:
    lower = message.lower()
    if any(word in lower for word in ("sad", "difficult", "hard day", "upset", "lonely", "stressed")):
        reply = "That sounds like a lot to carry. If you feel like talking about it, I'm here to listen. What has been on your mind?"
        emotion, intent, style, pace = "empathetic", "emotional_support", "calm", "gentle"
    elif any(word in lower for word in ("excited", "happy", "great", "awesome", "won")):
        reply = "That's lovely to hear. What part of it are you most excited about?"
        emotion, intent, style, pace = "joyful", "sharing_good_news", "upbeat", "normal"
    else:
        reply = f"I'm here with you. Tell me a little more about what you mean by: {message[:180]}"
        emotion, intent, style, pace = "curious", "conversation", "curious", "normal"
    return {"reply": reply, "emotion": emotion, "confidence": 0.62, "intent": intent, "delivery_style": style, "pace": pace}


def generate_reply(message: str, history: list[Message]) -> tuple[dict, bool]:
    if not settings.openai_api_key:
        return demo_reply(message), True

    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        base_url=settings.openai_base_url,
        temperature=0.7,
        timeout=30,
        max_retries=1,
    )
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for item in history[-12:]:
        if item.role == "user":
            messages.append(HumanMessage(content=item.content))
        elif item.role == "assistant":
            messages.append(AIMessage(content=item.content))
    messages.append(HumanMessage(content=f"Respond to this new user message. Return the required JSON object.\n\n{message}"))
    result = llm.invoke(messages)
    content = result.content
    if isinstance(content, list):
        content = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    raw = str(content).strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    data = json.loads(raw)
    allowed_emotions = {"empathetic", "calm", "curious", "encouraging", "joyful", "neutral"}
    allowed_styles = {"calm", "warm", "curious", "upbeat", "direct"}
    allowed_paces = {"gentle", "normal", "brisk"}
    return {
        "reply": str(data.get("reply", "I'm listening."))[:6000],
        "emotion": data.get("emotion") if data.get("emotion") in allowed_emotions else "neutral",
        "confidence": max(0.0, min(1.0, float(data.get("confidence", 0.5)))),
        "intent": str(data.get("intent", "conversation"))[:60],
        "delivery_style": data.get("delivery_style") if data.get("delivery_style") in allowed_styles else "warm",
        "pace": data.get("pace") if data.get("pace") in allowed_paces else "normal",
    }, False
