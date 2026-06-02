import secrets
import time
from urllib.parse import quote, urlparse, parse_qs

import httpx
from fastapi import status

from app.core.config import settings
from app.core.exceptions import AppException
from app.schemas.event import EventPosterUploadResponse

EVENT_POSTERS_BUCKET = "event-posters"
SIGNED_UPLOAD_EXPIRES_SECONDS = 600
ALLOWED_POSTER_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def create_event_poster_signed_upload(club_id: int, content_type: str) -> EventPosterUploadResponse:
    extension = ALLOWED_POSTER_TYPES.get(content_type)
    if extension is None:
        raise AppException("Only JPG, PNG, and WEBP files are allowed.", status.HTTP_422_UNPROCESSABLE_ENTITY)
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise AppException("Supabase poster upload is not configured", status.HTTP_500_INTERNAL_SERVER_ERROR)

    file_path = f"{club_id}_{int(time.time())}_{secrets.token_hex(3)}.{extension}"
    encoded_path = quote(file_path, safe="")
    storage_url = settings.supabase_url.rstrip("/")
    response = httpx.post(
        f"{storage_url}/storage/v1/object/upload/sign/{EVENT_POSTERS_BUCKET}/{encoded_path}",
        headers={
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Content-Type": "application/json",
        },
        json={"expiresIn": SIGNED_UPLOAD_EXPIRES_SECONDS},
        timeout=10,
    )

    if response.status_code >= 400:
        raise AppException("Could not create poster upload URL", status.HTTP_502_BAD_GATEWAY)

    data = response.json()
    token = _extract_signed_upload_token(data)
    signed_url = _extract_signed_upload_url(storage_url, data)
    if not token:
        raise AppException("Supabase did not return a poster upload token", status.HTTP_502_BAD_GATEWAY)
    if not signed_url:
        raise AppException("Supabase did not return a poster upload URL", status.HTTP_502_BAD_GATEWAY)

    return EventPosterUploadResponse(
        path=file_path,
        token=token,
        signed_url=signed_url,
        public_url=f"{storage_url}/storage/v1/object/public/{EVENT_POSTERS_BUCKET}/{encoded_path}",
    )


def _extract_signed_upload_token(data: dict) -> str | None:
    token = data.get("token")
    if isinstance(token, str) and token:
        return token

    signed_url = data.get("signedURL") or data.get("signedUrl") or data.get("url")
    if isinstance(signed_url, str):
        query = parse_qs(urlparse(signed_url).query)
        values = query.get("token")
        if values:
            return values[0]

    return None


def _extract_signed_upload_url(storage_url: str, data: dict) -> str | None:
    signed_url = data.get("signedUrl") or data.get("signedURL")
    if isinstance(signed_url, str) and signed_url:
        return signed_url if signed_url.startswith("http") else f"{storage_url}{signed_url}"

    url = data.get("url")
    if isinstance(url, str) and url:
        return url if url.startswith("http") else f"{storage_url}{url}"

    return None
