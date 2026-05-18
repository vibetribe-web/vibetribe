import logging

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppException
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import Token, TokenWithUser, UserCreate, UserLogin, UserRead
from app.services import auth_service, google_auth_service

router = APIRouter()
oauth = OAuth()
logger = logging.getLogger(__name__)

if settings.google_client_id and settings.google_client_secret:
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


def _ensure_google_oauth_configured() -> None:
    if not settings.google_client_id or not settings.google_client_secret:
        raise AppException("Google OAuth is not configured", status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    return auth_service.register_user(db, payload)


@router.post("/login", response_model=Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    return auth_service.create_login_token(user)


@router.post("/login/json", response_model=Token)
def login_user_json(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    return auth_service.login_user(db, payload)


@router.get("/google/login")
async def google_login(request: Request):
    _ensure_google_oauth_configured()
    logger.info("Google OAuth login route reached")
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri=settings.google_redirect_uri,
    )


@router.get("/google/callback", response_model=TokenWithUser)
async def google_callback(request: Request, db: Session = Depends(get_db)) -> TokenWithUser:
    _ensure_google_oauth_configured()
    logger.info("Google OAuth callback reached")

    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if user_info is None:
        user_info = await oauth.google.userinfo(token=token)

    user_email = user_info.get("email")
    if user_email:
        logger.info("Google OAuth user email received email=%s", user_email)
    return google_auth_service.login_or_create_google_user(db, dict(user_info))
