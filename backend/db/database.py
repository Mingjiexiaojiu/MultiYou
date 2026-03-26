import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Ensure data directory exists relative to cwd (backend/)
os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data"), exist_ok=True)

_db_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "multiyou.db")
)
DATABASE_URL = f"sqlite:///{_db_path}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
