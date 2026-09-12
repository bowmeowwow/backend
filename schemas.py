from datetime import date as date_type
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, model_validator

from models import ClinicCategory, PetCategory, ScheduleCategory


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    email: str
    password: str
    name: str
    phone: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    accessToken: str
    user: UserResponse


class MessageResponse(BaseModel):
    message: str


class PetCreateRequest(BaseModel):
    name: str
    category: PetCategory
    age: int
    birthDate: Optional[date_type] = None
    weight: Optional[float] = None


class PetUpdateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[PetCategory] = None
    age: Optional[int] = None
    birthDate: Optional[date_type] = None
    weight: Optional[float] = None


class PetResponse(BaseModel):
    id: int
    name: str
    category: PetCategory
    age: int
    birthDate: Optional[date_type] = None
    weight: Optional[float] = None


class ClinicResponse(BaseModel):
    id: int
    name: str
    category: ClinicCategory
    district: str
    address: str
    phone: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True


class InsurancePolicyResponse(BaseModel):
    insurerName: str
    monthlyPremium: int
    coverageLimit: int
    status: str


class ClaimCreateRequest(BaseModel):
    petId: int
    description: str
    amount: int


class ClaimResponse(BaseModel):
    id: int
    petId: int
    description: str
    amount: int
    status: str


class ChatRequest(BaseModel):
    message: str
    petId: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str


class RecommendRequest(BaseModel):
    latitude: float
    longitude: float
    category: Optional[ClinicCategory] = None
    petId: Optional[int] = None


class NearbyPlaceResponse(BaseModel):
    id: int
    name: str
    category: ClinicCategory
    address: str
    phone: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distanceKm: float


class RecommendResponse(BaseModel):
    reply: str
    places: List[NearbyPlaceResponse]


class ScheduleCreateRequest(BaseModel):
    petId: Optional[int] = None
    petName: Optional[str] = None
    date: date_type
    time: str
    title: str
    category: ScheduleCategory
    location: Optional[str] = None

    @model_validator(mode="after")
    def check_pet_reference(self):
        if self.petId is None and not self.petName:
            raise ValueError("petId 또는 petName 중 하나는 필요합니다.")
        return self


class ScheduleUpdateRequest(BaseModel):
    petId: Optional[int] = None
    petName: Optional[str] = None
    date: Optional[date_type] = None
    time: Optional[str] = None
    title: Optional[str] = None
    category: Optional[ScheduleCategory] = None
    location: Optional[str] = None


class ScheduleResponse(BaseModel):
    id: int
    petId: Optional[int] = None
    petName: Optional[str] = None
    date: date_type
    time: str
    title: str
    category: ScheduleCategory
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class NewsArticleResponse(BaseModel):
    id: int
    title: str
    summary: Optional[str] = None
    source: Optional[str] = None
    url: str
    publishedAt: Optional[datetime] = None
