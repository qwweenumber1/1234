from typing import Optional

from sqlalchemy.orm import Session
from .models import User
from .security import hash_password


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Return a user by email or None if not found."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, hashed_password: str, verification_token: str = None) -> User:
    """Create a new user with a hashed password and return the instance."""
    user = User(email=email, hashed_password=hashed_password, verification_token=verification_token)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def verify_user(db: Session, token: str) -> bool:
    user = db.query(User).filter(User.verification_token == token).first()
    if user:
        user.is_verified = 1
        user.verification_token = None
        db.commit()
        return True
    return False

def make_user_admin(db: Session, email: str) -> bool:
    user = get_user_by_email(db, email)
    if user:
        user.role = "admin"
        db.commit()
        db.refresh(user)
        return True
    return False
