from datetime import date as date_type
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Pet, Schedule, User
from schemas import MessageResponse, ScheduleCreateRequest, ScheduleResponse, ScheduleUpdateRequest

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


def _to_response(schedule: Schedule) -> ScheduleResponse:
    return ScheduleResponse(
        id=schedule.id,
        petId=schedule.pet_id,
        petName=schedule.pet_name,
        date=schedule.date,
        time=schedule.time,
        title=schedule.title,
        category=schedule.category,
    )


def _resolve_pet(
    pet_id: Optional[int], pet_name: Optional[str], current_user: User, db: Session
) -> Tuple[Optional[int], Optional[str]]:
    if pet_id is not None:
        pet = db.query(Pet).filter(Pet.id == pet_id, Pet.user_id == current_user.id).first()
        if pet is None:
            raise HTTPException(status_code=404, detail="반려동물을 찾을 수 없습니다.")
        return pet.id, pet.name
    return None, pet_name


def _get_owned_schedule(schedule_id: int, current_user: User, db: Session) -> Schedule:
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.user_id == current_user.id).first()
    if schedule is None:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
    return schedule


@router.post("", response_model=ScheduleResponse, status_code=201)
def create_schedule(
    payload: ScheduleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet_id, pet_name = _resolve_pet(payload.petId, payload.petName, current_user, db)
    schedule = Schedule(
        user_id=current_user.id,
        pet_id=pet_id,
        pet_name=pet_name,
        date=payload.date,
        time=payload.time,
        title=payload.title,
        category=payload.category,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return _to_response(schedule)


@router.get("", response_model=List[ScheduleResponse])
def list_schedules(
    from_: Optional[date_type] = Query(None, alias="from"),
    to: Optional[date_type] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Schedule).filter(Schedule.user_id == current_user.id)
    if from_ is not None:
        query = query.filter(Schedule.date >= from_)
    if to is not None:
        query = query.filter(Schedule.date <= to)
    return [_to_response(schedule) for schedule in query.all()]


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: int,
    payload: ScheduleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    schedule = _get_owned_schedule(schedule_id, current_user, db)

    if payload.petId is not None or payload.petName is not None:
        pet_id, pet_name = _resolve_pet(payload.petId, payload.petName, current_user, db)
        schedule.pet_id = pet_id
        schedule.pet_name = pet_name
    if payload.date is not None:
        schedule.date = payload.date
    if payload.time is not None:
        schedule.time = payload.time
    if payload.title is not None:
        schedule.title = payload.title
    if payload.category is not None:
        schedule.category = payload.category

    db.commit()
    db.refresh(schedule)
    return _to_response(schedule)


@router.delete("/{schedule_id}", response_model=MessageResponse)
def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    schedule = _get_owned_schedule(schedule_id, current_user, db)
    db.delete(schedule)
    db.commit()
    return MessageResponse(message="삭제되었습니다.")
