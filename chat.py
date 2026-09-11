import os
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from google import genai
from google.genai import errors as genai_errors
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import InsurancePolicy, Pet, User
from schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=503, detail="AI 챗봇이 설정되지 않았습니다.")
        _client = genai.Client(api_key=api_key)
    return _client


def _build_context(payload: ChatRequest, current_user: User, db: Session) -> str:
    lines = [f"사용자 이름: {current_user.name}"]

    if payload.petId is not None:
        pet = db.query(Pet).filter(Pet.id == payload.petId, Pet.user_id == current_user.id).first()
        if pet is None:
            raise HTTPException(status_code=404, detail="반려동물을 찾을 수 없습니다.")
        age = date.today().year - pet.birth_year
        lines.append(f"반려동물: {pet.name} ({pet.category.value}, {age}살)")

    policy = db.query(InsurancePolicy).filter(InsurancePolicy.user_id == current_user.id).first()
    if policy is not None:
        lines.append(
            f"가입 보험: {policy.insurer_name}, 월 보험료 {policy.monthly_premium}원, "
            f"보장한도 {policy.coverage_limit}원, 상태 {policy.status}"
        )

    return "\n".join(lines)


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    context = _build_context(payload, current_user, db)
    system_prompt = (
        "당신은 반려동물 건강 상담과 펫보험 안내를 돕는 어시스턴트입니다. "
        "아래 사용자 정보를 참고해 답변하세요.\n" + context
    )

    client = _get_client()
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=payload.message,
            config=genai.types.GenerateContentConfig(system_instruction=system_prompt),
        )
    except genai_errors.APIError:
        raise HTTPException(status_code=502, detail="AI 응답 생성에 실패했습니다.")

    return ChatResponse(reply=response.text)
