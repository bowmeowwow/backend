import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer, String

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
