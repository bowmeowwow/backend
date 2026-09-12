from sqlalchemy.orm import Session

from geocoding import geocode_address
from models import Clinic, ClinicCategory, InsurancePolicy, User
from security import hash_password

TEST_USER_EMAIL = "test"
TEST_USER_PASSWORD = "test1234"
TEST_USER_NAME = "이상준"


def seed_test_user(db: Session) -> None:
    if db.query(User).filter(User.email == TEST_USER_EMAIL).first():
        return
    db.add(
        User(
            name=TEST_USER_NAME,
            email=TEST_USER_EMAIL,
            hashed_password=hash_password(TEST_USER_PASSWORD),
        )
    )
    db.commit()


def seed_mock_clinics(db: Session) -> None:
    if db.query(Clinic).first():
        return

    clinics_data = [
        ("행복동물병원", ClinicCategory.VET, "강남구", "서울특별시 강남구 테헤란로 152", "02-111-2222"),
        ("사랑동물메디컬센터", ClinicCategory.VET, "강남구", "서울특별시 강남구 학동로 426", "02-222-3333"),
        ("튼튼동물병원", ClinicCategory.VET, "마포구", "서울특별시 마포구 월드컵로 212", "02-333-4444"),
        ("포시즌펫호텔", ClinicCategory.HOTEL, "송파구", "서울특별시 송파구 올림픽로 300", "02-444-5555"),
        ("멍뭉이미용실", ClinicCategory.GROOMING, "영등포구", "서울특별시 영등포구 63로 50", "02-555-6666"),
    ]

    for name, category, district, address, phone in clinics_data:
        coords = geocode_address(address)
        latitude, longitude = coords if coords else (None, None)
        db.add(
            Clinic(
                name=name,
                category=category,
                district=district,
                address=address,
                phone=phone,
                latitude=latitude,
                longitude=longitude,
            )
        )
    db.commit()


def seed_mock_insurance(db: Session) -> None:
    test_user = db.query(User).filter(User.email == TEST_USER_EMAIL).first()
    if test_user is None or db.query(InsurancePolicy).filter(InsurancePolicy.user_id == test_user.id).first():
        return

    db.add(
        InsurancePolicy(
            user_id=test_user.id,
            insurer_name="메리츠 펫보험",
            monthly_premium=15000,
            coverage_limit=3000000,
            status="ACTIVE",
        )
    )
    db.commit()
