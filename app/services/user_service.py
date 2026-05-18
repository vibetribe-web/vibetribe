from fastapi import status
from sqlalchemy import String, cast, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.branch import Branch
from app.models.college import College
from app.models.user import User
from app.schemas.user import UsernameUpdate, UsernameUpdateResponse, UserUpdate
from app.services.taxonomy_service import (
    get_or_create_branch,
    get_or_create_college,
    get_or_create_skills,
)


def list_users(db: Session, search: str | None = None) -> list[User]:
    statement = (
        select(User)
        .outerjoin(User.branch_ref)
        .outerjoin(User.college_ref)
        .order_by(User.name, User.id)
    )
    if search:
        term = f"%{search.strip().lower()}%"
        statement = statement.where(
            or_(
                User.name.ilike(term),
                User.username.ilike(term),
                Branch.name.ilike(term),
                College.name.ilike(term),
                cast(User.year, String).ilike(term),
            )
        )
    return list(db.scalars(statement))


def update_profile(db: Session, user: User, payload: UserUpdate) -> User:
    values = payload.model_dump(exclude_unset=True)
    if "name" in values:
        user.name = values["name"]
    if "college" in values:
        user.college_ref = get_or_create_college(db, values["college"])
    if "branch" in values:
        user.branch_ref = get_or_create_branch(db, values["branch"])
    if "year" in values:
        user.year = values["year"]
    if "skills" in values:
        user.skill_entities = get_or_create_skills(db, values["skills"])
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_username(db: Session, user: User, payload: UsernameUpdate) -> UsernameUpdateResponse:
    existing_user = db.scalar(
        select(User).where(User.username == payload.username, User.id != user.id)
    )
    if existing_user:
        raise AppException("Username already exists", status.HTTP_409_CONFLICT)

    user.username = payload.username
    db.add(user)
    db.commit()
    db.refresh(user)
    return UsernameUpdateResponse(
        message="Username updated successfully",
        username=user.username,
    )
