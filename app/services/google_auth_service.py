import logging
import secrets
from typing import Any

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import TokenWithUser
from app.services.auth_service import create_login_token

logger = logging.getLogger(__name__)


def _claim_value(user_info: dict[str, Any], key: str) -> str | None:
    value = user_info.get(key)
    return str(value).strip() if value else None


def login_or_create_google_user(db: Session, user_info: dict[str, Any]) -> TokenWithUser:
    google_id = _claim_value(user_info, "sub")
    email = _claim_value(user_info, "email")
    name = _claim_value(user_info, "name") or (email.split("@", 1)[0] if email else None)
    picture = _claim_value(user_info, "picture")
    email_verified = user_info.get("email_verified")

    if not google_id or not email:
        raise AppException("Google account did not provide required identity details", status.HTTP_400_BAD_REQUEST)
    if email_verified is False:
        raise AppException("Google email is not verified", status.HTTP_403_FORBIDDEN)

    normalized_email = email.lower()
    user = db.scalar(select(User).where(User.google_id == google_id))
    if user is None:
        user = db.scalar(select(User).where(User.email == normalized_email))
        if user is not None:
            logger.info("Linking Google account to existing user email=%s", normalized_email)
            user.google_id = google_id
            user.profile_image_url = picture
            if user.auth_provider == "email":
                user.auth_provider = "google"
        else:
            logger.info("Creating Google user email=%s", normalized_email)
            user = User(
                name=name or "Google User",
                email=normalized_email,
                password_hash=hash_password(secrets.token_urlsafe(32)),
                auth_provider="google",
                google_id=google_id,
                profile_image_url=picture,
            )
            db.add(user)
    else:
        logger.info("Logging in existing Google user email=%s", normalized_email)
        user.email = normalized_email
        user.name = name or user.name
        user.profile_image_url = picture

    db.commit()
    db.refresh(user)
    token = create_login_token(user)
    return TokenWithUser(
        access_token=token.access_token,
        token_type=token.token_type,
        user=user,
    )
