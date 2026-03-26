from db.database import SessionLocal
from models.db_models import Model


def seed_default_models(db):
    """Insert default model config if the table is empty."""
    if db.query(Model).count() == 0:
        default = Model(
            name="DeepSeek V3",
            model_id="deepseek-chat",
            provider="deepseek",
            endpoint="https://api.deepseek.com",
            api_key=None,
            config_json=None,
            is_local=False,
        )
        db.add(default)
        db.commit()
        print("[seed] Inserted default DeepSeek V3 model config")


def run_seed():
    db = SessionLocal()
    try:
        seed_default_models(db)
    finally:
        db.close()
