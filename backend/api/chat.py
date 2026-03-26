from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_current_user
from db.database import get_db
from models.db_models import Avatar as AvatarORM
from models.db_models import ChatLog, Persona as PersonaORM
from models.db_models import Session as SessionORM
from models.db_models import Model as ModelORM, User
from models.schemas import ChatLogResponse, ChatRequest, ChatResponse, SessionCreate, SessionResponse, SessionUpdate
from services.chat_service import build_messages, save_messages
from services.key_service import get_api_key
from services.model_provider import OpenAICompatProvider

router = APIRouter()


# ── Sessions ──────────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionResponse, status_code=201)
def create_session(
    body: SessionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    avatar = (
        db.query(AvatarORM)
        .filter(AvatarORM.id == body.avatar_id, AvatarORM.user_id == user.id)
        .first()
    )
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    session = SessionORM(avatar_id=body.avatar_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/avatars/{avatar_id}/sessions", response_model=List[SessionResponse])
def list_sessions(
    avatar_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    avatar = (
        db.query(AvatarORM)
        .filter(AvatarORM.id == avatar_id, AvatarORM.user_id == user.id)
        .first()
    )
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return (
        db.query(SessionORM)
        .filter(SessionORM.avatar_id == avatar_id)
        .order_by(SessionORM.updated_at.desc())
        .all()
    )


@router.put("/sessions/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: int,
    body: SessionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = _get_session_for_user(session_id, user.id, db)
    session.title = body.title
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions/{session_id}/logs", response_model=List[ChatLogResponse])
def get_logs(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_session_for_user(session_id, user.id, db)  # auth check
    return (
        db.query(ChatLog)
        .filter(ChatLog.session_id == session_id)
        .order_by(ChatLog.timestamp.asc())
        .all()
    )


# ── Chat ──────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = _get_session_for_user(body.session_id, user.id, db)
    avatar = db.query(AvatarORM).filter(AvatarORM.id == session.avatar_id).first()
    persona = db.query(PersonaORM).filter(PersonaORM.id == avatar.persona_id).first()
    model_cfg = db.query(ModelORM).filter(ModelORM.id == avatar.model_id).first()

    history = (
        db.query(ChatLog)
        .filter(ChatLog.session_id == body.session_id)
        .order_by(ChatLog.timestamp.asc())
        .all()
    )
    messages = build_messages(persona.system_prompt, history, body.message)

    api_key = None if model_cfg.is_local else get_api_key(model_cfg.id)
    provider = OpenAICompatProvider(
        endpoint=model_cfg.endpoint,
        model_id=model_cfg.model_id,
        api_key=api_key,
        is_local=model_cfg.is_local,
    )
    try:
        reply = provider.call(messages)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model error: {exc}")

    save_messages(db, body.session_id, body.message, reply)
    return ChatResponse(reply=reply, session_id=body.session_id)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_session_for_user(session_id: int, user_id: int, db: Session) -> SessionORM:
    """Return session, verifying the owning avatar belongs to user."""
    session = db.query(SessionORM).filter(SessionORM.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    avatar = db.query(AvatarORM).filter(
        AvatarORM.id == session.avatar_id,
        AvatarORM.user_id == user_id,
    ).first()
    if not avatar:
        raise HTTPException(status_code=403, detail="Access denied")
    return session
