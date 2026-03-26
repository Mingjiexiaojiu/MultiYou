from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user_id: int
    token: str
    onboarding_done: bool


# ── Model Config ──────────────────────────────────────────────────────────────

class ModelCreate(BaseModel):
    name: str
    model_id: str
    provider: str
    endpoint: str
    api_key: Optional[str] = None
    config_json: Optional[str] = None
    is_local: bool = False


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    model_id: Optional[str] = None
    provider: Optional[str] = None
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    config_json: Optional[str] = None
    is_local: Optional[bool] = None


class ModelResponse(BaseModel):
    id: int
    name: str
    model_id: str
    provider: str
    endpoint: str
    is_local: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ModelTestResponse(BaseModel):
    success: bool
    message: str
    latency_ms: Optional[int] = None


# ── Persona ───────────────────────────────────────────────────────────────────

class PersonaCreate(BaseModel):
    name: str
    system_prompt: str
    description: Optional[str] = None


class PersonaResponse(BaseModel):
    id: int
    name: str
    system_prompt: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Avatar ────────────────────────────────────────────────────────────────────

class AvatarResponse(BaseModel):
    id: int
    name: Optional[str]
    image_path: Optional[str]
    persona: PersonaResponse
    model: ModelResponse
    created_at: datetime

    class Config:
        from_attributes = True


# ── Session ───────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    avatar_id: int


class SessionUpdate(BaseModel):
    title: str


class SessionResponse(BaseModel):
    id: int
    avatar_id: int
    title: str
    start_time: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: int
    message: str


class ChatResponse(BaseModel):
    reply: str
    session_id: int


class ChatLogResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True


# ── Onboarding ────────────────────────────────────────────────────────────────

class OnboardingResponse(BaseModel):
    avatar_id: int
    message: str
