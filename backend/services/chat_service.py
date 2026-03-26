import datetime
from typing import List, Dict

from sqlalchemy.orm import Session

from models.db_models import ChatLog
from models.db_models import Session as DBSession


def build_messages(
    system_prompt: str,
    history: List[ChatLog],
    new_message: str,
) -> List[Dict[str, str]]:
    """Build messages array: system prompt + sliding window (last 20) + new user message."""
    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    window = history[-20:] if len(history) > 20 else history
    for log in window:
        messages.append({"role": log.role, "content": log.content})
    messages.append({"role": "user", "content": new_message})
    return messages


def save_messages(
    db: Session,
    session_id: int,
    user_msg: str,
    assistant_msg: str,
) -> None:
    """Persist both turns and bump session.updated_at."""
    now = datetime.datetime.utcnow()
    db.add(ChatLog(session_id=session_id, role="user", content=user_msg, timestamp=now))
    db.add(ChatLog(session_id=session_id, role="assistant", content=assistant_msg, timestamp=now))
    db.query(DBSession).filter(DBSession.id == session_id).update({"updated_at": now})
    db.commit()
