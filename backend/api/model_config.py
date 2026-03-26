import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_current_user
from db.database import get_db
from models.db_models import Model as ModelORM, User
from models.schemas import ModelCreate, ModelResponse, ModelTestResponse, ModelUpdate
from services.key_service import delete_api_key, get_api_key, store_api_key
from services.model_provider import OpenAICompatProvider

router = APIRouter()


@router.get("/models", response_model=List[ModelResponse])
def list_models(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return db.query(ModelORM).all()


@router.post("/models", response_model=ModelResponse, status_code=201)
def create_model(
    body: ModelCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    model = ModelORM(
        name=body.name,
        model_id=body.model_id,
        provider=body.provider,
        endpoint=body.endpoint,
        is_local=body.is_local,
        config_json=body.config_json,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    if body.api_key:
        store_api_key(model.id, body.api_key)
    return model


@router.put("/models/{model_id}", response_model=ModelResponse)
def update_model(
    model_id: int,
    body: ModelUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    model = db.query(ModelORM).filter(ModelORM.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    for field, value in body.model_dump(exclude_unset=True, exclude={"api_key"}).items():
        setattr(model, field, value)
    db.commit()
    db.refresh(model)
    if body.api_key is not None:
        store_api_key(model.id, body.api_key)
    return model


@router.delete("/models/{model_id}", status_code=204)
def delete_model(
    model_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    model = db.query(ModelORM).filter(ModelORM.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    delete_api_key(model.id)
    db.delete(model)
    db.commit()


@router.post("/models/{model_id}/test", response_model=ModelTestResponse)
def test_model(
    model_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    model = db.query(ModelORM).filter(ModelORM.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    api_key = None if model.is_local else get_api_key(model.id)
    provider = OpenAICompatProvider(
        endpoint=model.endpoint,
        model_id=model.model_id,
        api_key=api_key,
        is_local=model.is_local,
    )
    start = time.time()
    try:
        provider.call([{"role": "user", "content": "Hi"}], timeout=15.0)
        latency_ms = int((time.time() - start) * 1000)
        return ModelTestResponse(success=True, message="Connection successful", latency_ms=latency_ms)
    except Exception as exc:
        return ModelTestResponse(success=False, message=str(exc))
