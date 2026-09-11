from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import InsuranceClaim, InsurancePolicy, Pet, User
from schemas import ClaimCreateRequest, ClaimResponse, InsurancePolicyResponse

router = APIRouter(prefix="/api/insurance", tags=["insurance"])


def _claim_to_response(claim: InsuranceClaim) -> ClaimResponse:
    return ClaimResponse(
        id=claim.id,
        petId=claim.pet_id,
        description=claim.description,
        amount=claim.amount,
        status=claim.status,
    )


@router.post("/claims", response_model=ClaimResponse, status_code=201)
def create_claim(
    payload: ClaimCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pet = db.query(Pet).filter(Pet.id == payload.petId, Pet.user_id == current_user.id).first()
    if pet is None:
        raise HTTPException(status_code=404, detail="반려동물을 찾을 수 없습니다.")

    claim = InsuranceClaim(
        user_id=current_user.id,
        pet_id=payload.petId,
        description=payload.description,
        amount=payload.amount,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return _claim_to_response(claim)


@router.get("/claims", response_model=List[ClaimResponse])
def list_claims(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    claims = db.query(InsuranceClaim).filter(InsuranceClaim.user_id == current_user.id).all()
    return [_claim_to_response(claim) for claim in claims]


@router.get("/{user_id}", response_model=InsurancePolicyResponse)
def get_policy(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="다른 유저의 정보에 접근할 수 없습니다.")

    policy = db.query(InsurancePolicy).filter(InsurancePolicy.user_id == user_id).first()
    if policy is None:
        raise HTTPException(status_code=404, detail="가입한 보험이 없습니다.")

    return InsurancePolicyResponse(
        insurerName=policy.insurer_name,
        monthlyPremium=policy.monthly_premium,
        coverageLimit=policy.coverage_limit,
        status=policy.status,
    )
