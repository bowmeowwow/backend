import os
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from google import genai
from google.genai import errors as genai_errors
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from distance import haversine_km
from models import Clinic, InsurancePolicy, Pet, User
from schemas import ChatRequest, ChatResponse, NearbyPlaceResponse, RecommendRequest, RecommendResponse

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


@router.post("/recommend", response_model=RecommendResponse)
def recommend_places(
    payload: RecommendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Clinic).filter(Clinic.latitude.isnot(None), Clinic.longitude.isnot(None))
    if payload.category is not None:
        query = query.filter(Clinic.category == payload.category)

    nearby = sorted(
        (
            (clinic, haversine_km(payload.latitude, payload.longitude, clinic.latitude, clinic.longitude))
            for clinic in query.all()
        ),
        key=lambda pair: pair[1],
    )[:5]

    places = [
        NearbyPlaceResponse(
            id=clinic.id,
            name=clinic.name,
            category=clinic.category,
            address=clinic.address,
            phone=clinic.phone,
            latitude=clinic.latitude,
            longitude=clinic.longitude,
            distanceKm=round(distance_km, 2),
        )
        for clinic, distance_km in nearby
    ]

    pet_context = ""
    if payload.petId is not None:
        pet = db.query(Pet).filter(Pet.id == payload.petId, Pet.user_id == current_user.id).first()
        if pet is None:
            raise HTTPException(status_code=404, detail="반려동물을 찾을 수 없습니다.")
        age = date.today().year - pet.birth_year
        pet_context = f"\n반려동물: {pet.name} ({pet.category.value}, {age}살)"

    if not places:
        return RecommendResponse(reply="근처에 등록된 장소가 없어요. 다른 지역으로 다시 찾아볼까요?", places=[])

    places_text = "\n".join(
        f"- {place.name} ({place.category.value}, {place.distanceKm}km, {place.address})" for place in places
    )
    system_prompt = (
        "당신은 반려동물 보호자를 돕는 AI 동물 도우미입니다. "
        "아래 사용자 주변 장소 목록만 근거로, 친근한 말투로 1~2곳을 추천해주세요."
        f"{pet_context}\n\n주변 장소:\n{places_text}"
    )

    try:
        client = _get_client()
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents="지금 위치 근처에 어디로 가면 좋을지 추천해줘",
            config=genai.types.GenerateContentConfig(system_instruction=system_prompt),
        )
        reply = response.text
    except (HTTPException, genai_errors.APIError):
        reply = "추천 문구 생성엔 실패했지만, 근처 장소 목록은 확인하실 수 있어요."

    return RecommendResponse(reply=reply, places=places)
