from sqlalchemy.orm import Session

from models import User
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
