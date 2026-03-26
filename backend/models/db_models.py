from db.database import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    onboarding_done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())


class Persona(Base):
    __tablename__ = "persona"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    name = Column(String, nullable=False)
    system_prompt = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())


class Model(Base):
    __tablename__ = "model"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    model_id = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    api_key = Column(String)           # keyring reference identifier (not plaintext)
    config_json = Column(Text)         # optional JSON for extra config
    is_local = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())


class Avatar(Base):
    __tablename__ = "avatar"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    persona_id = Column(Integer, ForeignKey("persona.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("model.id"), nullable=False)
    name = Column(String)
    image_path = Column(String)
    created_at = Column(DateTime, default=func.now())

    persona = relationship("Persona", lazy="joined", foreign_keys=[persona_id])
    model = relationship("Model", lazy="joined", foreign_keys=[model_id])


class Session(Base):
    __tablename__ = "session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    avatar_id = Column(Integer, ForeignKey("avatar.id"), nullable=False)
    title = Column(String, default="新对话")
    start_time = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ChatLog(Base):
    __tablename__ = "chat_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("session.id"), nullable=False)
    role = Column(String, nullable=False)   # 'user' | 'assistant' | 'system'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())
