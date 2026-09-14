import os
from datetime import date
from typing import List, Optional, Tuple

import requests
from fastapi import APIRouter, Depends, HTTPException
from google import genai
from google.genai import errors as genai_errors
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from distance import haversine_km
from models import Clinic, ClinicCategory, InsurancePolicy, Pet, User
from schemas import (
    ChatRequest,
    ChatResponse,
    CompareResponse,
    NearbyPlaceResponse,
    RecommendRequest,
    RecommendResponse,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])

_client = None

LOCATION_WORDS = ["주변", "근처", "가까운", "인근"]
PLACE_WORDS = ["병원", "동물병원", "호텔", "펫호텔", "미용실", "미용", "놀 곳", "놀곳", "갈 곳", "갈곳", "데려갈"]
CATEGORY_WORDS = {
    ClinicCategory.VET: ["병원", "동물병원"],
    ClinicCategory.HOTEL: ["호텔", "펫호텔"],
    ClinicCategory.GROOMING: ["미용실", "미용"],
}

# Groq (groq.com fast inference), not xAI's Grok - initially built for Grok, but that
# account had no credits, and the user handed over a Groq key instead. Verified against
# a real successful response.
GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=503, detail="AI 챗봇이 설정되지 않았습니다.")
        _client = genai.Client(api_key=api_key)
    return _client


def _wants_nearby_recommendation(message: str) -> bool:
    has_location_word = any(word in message for word in LOCATION_WORDS)
    has_place_word = any(word in message for word in PLACE_WORDS)
    has_recommend_word = "추천" in message
    return (has_location_word and has_place_word) or (has_recommend_word and has_place_word)


def _detect_category(message: str) -> Optional[ClinicCategory]:
    for category, words in CATEGORY_WORDS.items():
        if any(word in message for word in words):
            return category
    return None


def _find_nearby_places(
    db: Session, latitude: float, longitude: float, category: Optional[ClinicCategory]
) -> List[NearbyPlaceResponse]:
    query = db.query(Clinic).filter(Clinic.latitude.isnot(None), Clinic.longitude.isnot(None))
    if category is not None:
        query = query.filter(Clinic.category == category)

    nearby = sorted(
        (
            (clinic, haversine_km(latitude, longitude, clinic.latitude, clinic.longitude))
            for clinic in query.all()
        ),
        key=lambda pair: pair[1],
    )[:5]

    return [
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


def _pet_context_line(pet_id: Optional[int], current_user: User, db: Session) -> str:
    if pet_id is None:
        return ""
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.user_id == current_user.id).first()
    if pet is None:
        raise HTTPException(status_code=404, detail="반려동물을 찾을 수 없습니다.")
    age = date.today().year - pet.birth_year
    return f"\n반려동물: {pet.name} ({pet.category.value}, {age}살)"


def _build_context(payload: ChatRequest, current_user: User, db: Session) -> str:
    lines = [f"사용자 이름: {current_user.name}"]

    pet_line = _pet_context_line(payload.petId, current_user, db)
    if pet_line:
        lines.append(pet_line.strip())

    policy = db.query(InsurancePolicy).filter(InsurancePolicy.user_id == current_user.id).first()
    if policy is not None:
        lines.append(
            f"가입 보험: {policy.insurer_name}, 월 보험료 {policy.monthly_premium}원, "
            f"보장한도 {policy.coverage_limit}원, 상태 {policy.status}"
        )

    return "\n".join(lines)


def _resolve_prompt(
    payload: ChatRequest, current_user: User, db: Session
) -> Tuple[Optional[List[NearbyPlaceResponse]], Optional[str], Optional[str]]:
    """Returns (places, system_prompt, early_reply).

    If early_reply is set, that's the final answer and no LLM call is needed
    (missing location permission, or no places found nearby).
    """
    if _wants_nearby_recommendation(payload.message):
        if payload.latitude is None or payload.longitude is None:
            return None, None, "근처 장소를 추천해드리려면 위치 정보가 필요해요! 위치 권한을 허용해 주세요."

        category = _detect_category(payload.message)
        places = _find_nearby_places(db, payload.latitude, payload.longitude, category)
        if not places:
            return [], None, "근처에 등록된 장소가 없어요. 다른 지역으로 다시 찾아볼까요?"

        pet_context = _pet_context_line(payload.petId, current_user, db)
        places_text = "\n".join(
            f"- {place.name} ({place.category.value}, {place.distanceKm}km, {place.address})" for place in places
        )
        system_prompt = (
            "당신은 반려동물 보호자를 돕는 AI 동물 도우미입니다. "
            "아래 사용자 주변 장소 목록만 근거로, 친근한 말투로 1~2곳을 추천해주세요."
            f"{pet_context}\n\n주변 장소:\n{places_text}"
        )
        return places, system_prompt, None

    context = _build_context(payload, current_user, db)
    system_prompt = (
        "당신은 반려동물 건강 상담과 펫보험 안내를 돕는 어시스턴트입니다. "
        "아래 사용자 정보를 참고해 답변하세요.\n" + context
    )
    return None, system_prompt, None


def _generate(message: str, system_prompt: str) -> str:
    client = _get_client()
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=message,
        config=genai.types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return response.text


def _call_groq(message: str, system_prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Groq 비교 기능을 사용할 수 없습니다 (API 키가 설정되지 않았습니다)."

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return "Groq 응답 생성에 실패했습니다."


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    places, system_prompt, early_reply = _resolve_prompt(payload, current_user, db)
    if early_reply is not None:
        return ChatResponse(reply=early_reply, places=places)

    try:
        reply = _generate(payload.message, system_prompt)
    except genai_errors.APIError:
        if places is not None:
            reply = "추천 문구 생성엔 실패했지만, 근처 장소 목록은 확인하실 수 있어요."
        else:
            raise HTTPException(status_code=502, detail="AI 응답 생성에 실패했습니다.")

    return ChatResponse(reply=reply, places=places)


@router.post("/compare", response_model=CompareResponse)
def compare_chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    places, system_prompt, early_reply = _resolve_prompt(payload, current_user, db)
    if early_reply is not None:
        return CompareResponse(places=places, gemini=early_reply, groq=early_reply)

    try:
        gemini_reply = _generate(payload.message, system_prompt)
    except genai_errors.APIError:
        gemini_reply = "Gemini 응답 생성에 실패했습니다."

    groq_reply = _call_groq(payload.message, system_prompt)

    return CompareResponse(places=places, gemini=gemini_reply, groq=groq_reply)


@router.post("/recommend", response_model=RecommendResponse)
def recommend_places(
    payload: RecommendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    places = _find_nearby_places(db, payload.latitude, payload.longitude, payload.category)
    pet_context = _pet_context_line(payload.petId, current_user, db)

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
        reply = _generate("지금 위치 근처에 어디로 가면 좋을지 추천해줘", system_prompt)
    except genai_errors.APIError:
        reply = "추천 문구 생성엔 실패했지만, 근처 장소 목록은 확인하실 수 있어요."

    return RecommendResponse(reply=reply, places=places)
