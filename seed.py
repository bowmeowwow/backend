from sqlalchemy.orm import Session

from models import Clinic, ClinicPrice, InsurancePolicy, User
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

    clinics = [
        Clinic(name="행복동물병원", district="강남구", address="서울특별시 강남구 테헤란로 152", phone="02-111-2222"),
        Clinic(name="사랑동물메디컬센터", district="강남구", address="서울특별시 강남구 학동로 426", phone="02-222-3333"),
        Clinic(name="튼튼동물병원", district="마포구", address="서울특별시 마포구 월드컵로 212", phone="02-333-4444"),
    ]
    db.add_all(clinics)
    db.commit()

    db.add_all(
        [
            ClinicPrice(clinic_id=clinics[0].id, procedure="기본 건강검진", price=30000),
            ClinicPrice(clinic_id=clinics[0].id, procedure="예방접종", price=20000),
            ClinicPrice(clinic_id=clinics[0].id, procedure="스케일링", price=150000),
            ClinicPrice(clinic_id=clinics[1].id, procedure="기본 건강검진", price=35000),
            ClinicPrice(clinic_id=clinics[1].id, procedure="예방접종", price=25000),
            ClinicPrice(clinic_id=clinics[2].id, procedure="기본 건강검진", price=25000),
            ClinicPrice(clinic_id=clinics[2].id, procedure="스케일링", price=120000),
        ]
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
