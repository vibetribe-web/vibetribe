from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin
from app.services.taxonomy_service import (
    get_or_create_branch,
    get_or_create_college,
    get_or_create_skills,
)


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or not verify_password(password, user.password_hash):
        raise AppException("Invalid email or password", status.HTTP_401_UNAUTHORIZED)
    return user


def register_user(db: Session, payload: UserCreate) -> User:
    existing_user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing_user:
        raise AppException(
            "A user with this email already exists",
            status.HTTP_409_CONFLICT,
        )

    user = User(
        name=payload.name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        college_ref=get_or_create_college(db, payload.college),
        branch_ref=get_or_create_branch(db, payload.branch),
        year=payload.year,
    )
    user.skill_entities = get_or_create_skills(db, payload.skills)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_login_token(user: User) -> Token:
    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token)


def login_user(db: Session, payload: UserLogin) -> Token:
    user = authenticate_user(db, payload.email, payload.password)
    return create_login_token(user)
