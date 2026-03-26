import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db.database import engine, Base
from db.seed import run_seed

# Import all models so SQLAlchemy can discover them before create_all
import models.db_models  # noqa: F401

from api import auth, avatar, chat, model_config, onboarding

# ── App setup ────────────────────────────────────────────────────────────────

app = FastAPI(title="MultiYou API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "app://.", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    run_seed()

    # Ensure avatar storage directory exists
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "assets", "avatar"), exist_ok=True)


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Static files (avatar images) ─────────────────────────────────────────────

_assets_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "assets")
)
if os.path.isdir(_assets_dir):
    app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")


# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(avatar.router, prefix="/api", tags=["avatar"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(model_config.router, prefix="/api", tags=["model"])
app.include_router(onboarding.router, prefix="/api", tags=["onboarding"])
