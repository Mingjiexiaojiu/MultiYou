from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.deps import get_current_user
from db.database import get_db
from models.db_models import Model as ModelORM, Persona as PersonaORM, User
from models.schemas import OnboardingResponse
from services.avatar_service import create_avatar
from services.key_service import store_api_key

router = APIRouter()


@router.post("/onboarding/setup", response_model=OnboardingResponse)
async def onboarding_setup(
    # Model config
    model_name: str = Form(...),
    provider: str = Form(...),
    endpoint: str = Form(...),
    model_id_str: str = Form(...),
    is_local: bool = Form(False),
    api_key: str = Form(""),
    # Persona / avatar
    avatar_name: str = Form(...),
    persona_name: str = Form(...),
    system_prompt: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.onboarding_done:
        raise HTTPException(status_code=400, detail="Onboarding already completed")

    # 1. Create model config
    model = ModelORM(
        name=model_name,
        model_id=model_id_str,
        provider=provider,
        endpoint=endpoint,
        is_local=is_local,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    if api_key:
        store_api_key(model.id, api_key)

    # 2. Create persona
    persona = PersonaORM(
        user_id=user.id,
        name=persona_name,
        system_prompt=system_prompt,
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)

    # 3. Process image & create avatar
    image_bytes = await image.read()
    content_type = image.content_type or "image/jpeg"
    try:
        avatar = create_avatar(
            db=db,
            user_id=user.id,
            name=avatar_name,
            persona_id=persona.id,
            model_id=model.id,
            image_bytes=image_bytes,
            content_type=content_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # 4. Mark onboarding complete
    user.onboarding_done = True
    db.commit()

    return OnboardingResponse(avatar_id=avatar.id, message="Onboarding complete")
