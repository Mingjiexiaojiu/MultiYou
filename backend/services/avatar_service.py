import os

from sqlalchemy.orm import Session

from models.db_models import Avatar as AvatarModel
from services.image_service import pixelate_avatar, validate_image


def _avatar_dir() -> str:
    base = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "assets", "avatar")
    )
    os.makedirs(base, exist_ok=True)
    return base


def create_avatar(
    db: Session,
    user_id: int,
    name: str,
    persona_id: int,
    model_id: int,
    image_bytes: bytes,
    content_type: str,
) -> AvatarModel:
    validate_image(image_bytes, content_type)

    avatar = AvatarModel(
        user_id=user_id,
        name=name,
        persona_id=persona_id,
        model_id=model_id,
    )
    db.add(avatar)
    db.flush()  # obtain avatar.id before writing file

    output_path = os.path.join(_avatar_dir(), f"{avatar.id}.png")
    pixelate_avatar(image_bytes, output_path)
    avatar.image_path = f"/assets/avatar/{avatar.id}.png"

    db.commit()
    db.refresh(avatar)
    return avatar
