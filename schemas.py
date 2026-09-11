from typing import Optional

from pydantic import BaseModel

from models import PetCategory


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    email: str
    password: str
    name: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str

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


class PetUpdateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[PetCategory] = None
    age: Optional[int] = None


class PetResponse(BaseModel):
    id: int
    name: str
    category: PetCategory
    age: int


class ClinicResponse(BaseModel):
    id: int
    name: str
    district: str
    address: str
    phone: str

    class Config:
        from_attributes = True


class ClinicPriceResponse(BaseModel):
    procedure: str
    price: int

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
