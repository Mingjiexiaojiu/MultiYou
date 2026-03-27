from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.deps import get_current_user
from db.database import get_db
from models.db_models import Avatar as AvatarORM, Persona as PersonaORM, User
from models.schemas import AvatarResponse, PersonaCreate, PersonaResponse
from services.avatar_service import create_avatar

router = APIRouter()


# ── Personas ──────────────────────────────────────────────────────────────────

@router.post("/personas", response_model=PersonaResponse, status_code=201)
def create_persona(
    body: PersonaCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    persona = PersonaORM(
        user_id=user.id,
        name=body.name,
        system_prompt=body.system_prompt,
        description=body.description,
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


@router.get("/personas", response_model=List[PersonaResponse])
def list_personas(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(PersonaORM).filter(PersonaORM.user_id == user.id).all()


# ── Avatars ───────────────────────────────────────────────────────────────────

@router.post("/avatars", response_model=AvatarResponse, status_code=201)
async def create_avatar_endpoint(
    name: str = Form(...),
    persona_id: int = Form(...),
    model_id: int = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    image_bytes = None
    content_type = None
    if image:
        image_bytes = await image.read()
        content_type = image.content_type or "image/jpeg"
    try:
        avatar = create_avatar(
            db=db,
            user_id=user.id,
            name=name,
            persona_id=persona_id,
            model_id=model_id,
            image_bytes=image_bytes,
            content_type=content_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return avatar


@router.get("/avatars", response_model=List[AvatarResponse])
def list_avatars(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(AvatarORM).filter(AvatarORM.user_id == user.id).all()


@router.get("/avatars/{avatar_id}", response_model=AvatarResponse)
def get_avatar(
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
    return avatar
