from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Pet, User
from schemas import MessageResponse, PetCreateRequest, PetResponse, PetUpdateRequest

router = APIRouter(prefix="/api/pets", tags=["pets"])


def _to_response(pet: Pet) -> PetResponse:
    return PetResponse(
        id=pet.id,
        name=pet.name,
        category=pet.category,
        age=date.today().year - pet.birth_year,
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
