import enum

from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, String

from database import Base


class PetCategory(str, enum.Enum):
    CAT = "CAT"
    DOG = "DOG"
    OTHER = "OTHER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)


class Pet(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(Enum(PetCategory), nullable=False)
    birth_year = Column(Integer, nullable=False)


class Clinic(Base):
    __tablename__ = "clinics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    district = Column(String(100), nullable=False, index=True)
    address = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)


class ClinicPrice(Base):
    __tablename__ = "clinic_prices"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    procedure = Column(String(255), nullable=False)
    price = Column(Integer, nullable=False)


class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    insurer_name = Column(String(255), nullable=False)
    monthly_premium = Column(Integer, nullable=False)
    coverage_limit = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="ACTIVE")


class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")


class ScheduleCategory(str, enum.Enum):
    VACCINATION = "VACCINATION"
    CHECKUP = "CHECKUP"
    GROOMING = "GROOMING"
    MEDICATION = "MEDICATION"
    OTHER = "OTHER"


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=True, index=True)
    pet_name = Column(String(255), nullable=True)
    date = Column(Date, nullable=False, index=True)
    time = Column(String(5), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(Enum(ScheduleCategory), nullable=False)
    location = Column(String(255), nullable=True)
