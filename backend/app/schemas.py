from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=6000)
    session_id: str | None = None


class Emotion(BaseModel):
    label: str = "warm"
    confidence: float = Field(default=0.6, ge=0, le=1)


class Delivery(BaseModel):
    style: str = "natural"
    pace: str = "normal"


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    emotion: Emotion
    intent: str
    delivery: Delivery
    demo_mode: bool = False


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    emotion: str
    intent: str

    model_config = {"from_attributes": True}


class SessionOut(BaseModel):
    id: str
    title: str

    model_config = {"from_attributes": True}
