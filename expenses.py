from datetime import date as date_type
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Expense, Pet, User
from schemas import (
    ExpenseCreateRequest,
    ExpenseResponse,
    ExpenseSummaryResponse,
    ExpenseUpdateRequest,
    MessageResponse,
    PetExpenseSummary,
)

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


def _to_response(expense: Expense) -> ExpenseResponse:
    return ExpenseResponse(
        id=expense.id,
        petId=expense.pet_id,
        description=expense.description,
        amount=expense.amount,
        date=expense.date,
    )


def _get_owned_expense(expense_id: int, current_user: User, db: Session) -> Expense:
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == current_user.id).first()
    if expense is None:
        raise HTTPException(status_code=404, detail="지출 내역을 찾을 수 없습니다.")
    return expense


def _month_range(month: str) -> Tuple[date_type, date_type]:
    try:
        year_str, month_str = month.split("-")
        year, mon = int(year_str), int(month_str)
        start = date_type(year, mon, 1)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="month는 YYYY-MM 형식이어야 합니다.")
    end = date_type(year + 1, 1, 1) if mon == 12 else date_type(year, mon + 1, 1)
    return start, end


@router.post("", response_model=ExpenseResponse, status_code=201)
def create_expense(
    payload: ExpenseCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = db.query(Pet).filter(Pet.id == payload.petId, Pet.user_id == current_user.id).first()
    if pet is None:
        raise HTTPException(status_code=404, detail="반려동물을 찾을 수 없습니다.")

    expense = Expense(
        user_id=current_user.id,
        pet_id=payload.petId,
        description=payload.description,
        amount=payload.amount,
        date=payload.date or date_type.today(),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return _to_response(expense)


@router.get("", response_model=List[ExpenseResponse])
def list_expenses(
    petId: Optional[int] = Query(None),
    month: Optional[str] = Query(None, description="YYYY-MM"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Expense).filter(Expense.user_id == current_user.id)
    if petId is not None:
        query = query.filter(Expense.pet_id == petId)
    if month is not None:
        start, end = _month_range(month)
        query = query.filter(Expense.date >= start, Expense.date < end)
    expenses = query.order_by(Expense.date.desc(), Expense.id.desc()).all()
    return [_to_response(expense) for expense in expenses]


@router.get("/summary", response_model=ExpenseSummaryResponse)
def expense_summary(
    month: str = Query(..., description="YYYY-MM"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start, end = _month_range(month)
    expenses = (
        db.query(Expense)
        .filter(Expense.user_id == current_user.id, Expense.date >= start, Expense.date < end)
        .all()
    )

    totals_by_pet = {}
    for expense in expenses:
        totals_by_pet[expense.pet_id] = totals_by_pet.get(expense.pet_id, 0) + expense.amount

    pets = db.query(Pet).filter(Pet.id.in_(totals_by_pet.keys())).all() if totals_by_pet else []
    pet_names = {pet.id: pet.name for pet in pets}

    by_pet = [
        PetExpenseSummary(petId=pet_id, petName=pet_names.get(pet_id, ""), total=total)
        for pet_id, total in totals_by_pet.items()
    ]
    by_pet.sort(key=lambda item: item.total, reverse=True)

    return ExpenseSummaryResponse(month=month, total=sum(totals_by_pet.values()), byPet=by_pet)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expense = _get_owned_expense(expense_id, current_user, db)
    if payload.description is not None:
        expense.description = payload.description
    if payload.amount is not None:
        expense.amount = payload.amount
    if payload.date is not None:
        expense.date = payload.date
    db.commit()
    db.refresh(expense)
    return _to_response(expense)


@router.delete("/{expense_id}", response_model=MessageResponse)
def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expense = _get_owned_expense(expense_id, current_user, db)
    db.delete(expense)
    db.commit()
    return MessageResponse(message="삭제되었습니다.")
