from datetime import date
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Pet, User
from schemas import MessageResponse, PetCreateRequest, PetResponse, PetUpdateRequest

router = APIRouter(prefix="/api/pets", tags=["pets"])

MAX_PHOTO_SIZE = 3 * 1024 * 1024
ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _to_response(pet: Pet) -> PetResponse:
    return PetResponse(
        id=pet.id,
        name=pet.name,
        category=pet.category,
        age=date.today().year - pet.birth_year,
        birthDate=pet.birth_date,
        weight=pet.weight,
        photoUrl=f"/api/pets/{pet.id}/photo" if pet.photo is not None else None,
    )


def _get_owned_pet(pet_id: int, current_user: User, db: Session) -> Pet:
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.user_id == current_user.id).first()
    if pet is None:
        raise HTTPException(status_code=404, detail="반려동물을 찾을 수 없습니다.")
    return pet


@router.post("", response_model=PetResponse, status_code=201)
def create_pet(
    payload: PetCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = Pet(
        user_id=current_user.id,
        name=payload.name,
        category=payload.category,
        birth_year=date.today().year - payload.age,
        birth_date=payload.birthDate,
        weight=payload.weight,
    )
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return _to_response(pet)


@router.get("", response_model=List[PetResponse])
def list_pets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pets = db.query(Pet).filter(Pet.user_id == current_user.id).all()
    return [_to_response(pet) for pet in pets]


@router.patch("/{pet_id}", response_model=PetResponse)
def update_pet(
    pet_id: int,
    payload: PetUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = _get_owned_pet(pet_id, current_user, db)
    if payload.name is not None:
        pet.name = payload.name
    if payload.category is not None:
        pet.category = payload.category
    if payload.age is not None:
        pet.birth_year = date.today().year - payload.age
    if payload.birthDate is not None:
        pet.birth_date = payload.birthDate
    if payload.weight is not None:
        pet.weight = payload.weight
    db.commit()
    db.refresh(pet)
    return _to_response(pet)


@router.delete("/{pet_id}", response_model=MessageResponse)
def delete_pet(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = _get_owned_pet(pet_id, current_user, db)
    db.delete(pet)
    db.commit()
    return MessageResponse(message="삭제되었습니다.")


@router.put("/{pet_id}/photo", response_model=PetResponse)
async def upload_pet_photo(
    pet_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = _get_owned_pet(pet_id, current_user, db)
    if file.content_type not in ALLOWED_PHOTO_TYPES:
        raise HTTPException(status_code=400, detail="jpeg/png/webp 이미지만 업로드할 수 있습니다.")

    content = await file.read()
    if len(content) > MAX_PHOTO_SIZE:
        raise HTTPException(status_code=413, detail="이미지 용량은 3MB 이하만 가능합니다.")

    pet.photo = content
    pet.photo_content_type = file.content_type
    db.commit()
    db.refresh(pet)
    return _to_response(pet)


@router.get("/{pet_id}/photo")
def get_pet_photo(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = _get_owned_pet(pet_id, current_user, db)
    if pet.photo is None:
        raise HTTPException(status_code=404, detail="등록된 사진이 없습니다.")
    return Response(content=pet.photo, media_type=pet.photo_content_type or "image/jpeg")


@router.delete("/{pet_id}/photo", response_model=PetResponse)
def delete_pet_photo(
    pet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = _get_owned_pet(pet_id, current_user, db)
    pet.photo = None
    pet.photo_content_type = None
    db.commit()
    db.refresh(pet)
    return _to_response(pet)
