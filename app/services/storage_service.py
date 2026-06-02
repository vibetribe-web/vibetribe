import secrets
import time
from urllib.parse import quote

import httpx
from fastapi import UploadFile, status

from app.core.config import settings
from app.core.exceptions import AppException
from app.schemas.event import EventPosterUploadResponse

EVENT_POSTERS_BUCKET = "event-posters"
MAX_POSTER_BYTES = 2 * 1024 * 1024
ALLOWED_POSTER_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


async def upload_event_poster(club_id: int, poster: UploadFile) -> EventPosterUploadResponse:
    content_type = poster.content_type or ""
    extension = _validate_poster_type(content_type)
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise AppException("Supabase poster upload is not configured", status.HTTP_500_INTERNAL_SERVER_ERROR)

    data = await poster.read(MAX_POSTER_BYTES + 1)
    if len(data) > MAX_POSTER_BYTES:
        raise AppException("Poster size must be less than 2 MB.", status.HTTP_422_UNPROCESSABLE_ENTITY)

    _ensure_event_posters_bucket()
    file_path = _build_poster_path(club_id, extension)
    encoded_path = quote(file_path, safe="")
    storage_url = settings.supabase_url.rstrip("/")
    response = httpx.post(
        f"{storage_url}/storage/v1/object/{EVENT_POSTERS_BUCKET}/{encoded_path}",
        headers={
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Content-Type": content_type,
            "Cache-Control": "31536000",
            "x-upsert": "false",
        },
        content=data,
        timeout=20,
    )
    if response.status_code >= 400:
        raise AppException("Could not upload poster.", status.HTTP_502_BAD_GATEWAY)

    return EventPosterUploadResponse(
        path=file_path,
        public_url=f"{storage_url}/storage/v1/object/public/{EVENT_POSTERS_BUCKET}/{encoded_path}",
    )


def _validate_poster_type(content_type: str) -> str:
    extension = ALLOWED_POSTER_TYPES.get(content_type)
    if extension is None:
        raise AppException("Only JPG, PNG, and WEBP files are allowed.", status.HTTP_422_UNPROCESSABLE_ENTITY)
    return extension


def _build_poster_path(club_id: int, extension: str) -> str:
    return f"{club_id}_{int(time.time())}_{secrets.token_hex(3)}.{extension}"


def _ensure_event_posters_bucket() -> None:
    storage_url = settings.supabase_url.rstrip("/")
    response = _supabase_storage_get(f"{storage_url}/storage/v1/bucket/{EVENT_POSTERS_BUCKET}")
    if response.status_code < 400:
        return

    if not _is_missing_bucket_response(response):
        raise AppException("Could not verify poster storage bucket", status.HTTP_502_BAD_GATEWAY)

    create_response = _supabase_storage_post(
        f"{storage_url}/storage/v1/bucket",
        json={
            "id": EVENT_POSTERS_BUCKET,
            "name": EVENT_POSTERS_BUCKET,
            "public": True,
            "file_size_limit": MAX_POSTER_BYTES,
            "allowed_mime_types": sorted(ALLOWED_POSTER_TYPES),
        },
    )
    if create_response.status_code >= 400:
        raise AppException("Could not create poster storage bucket", status.HTTP_502_BAD_GATEWAY)


def _is_missing_bucket_response(response: httpx.Response) -> bool:
    if response.status_code == 404:
        return True

    try:
        data = response.json()
    except ValueError:
        return False

    return (
        data.get("statusCode") == "404"
        or data.get("statusCode") == 404
        or data.get("message") == "Bucket not found"
    )


def _supabase_storage_get(url: str) -> httpx.Response:
    return httpx.get(url, headers=_supabase_storage_headers(), timeout=10)


def _supabase_storage_post(url: str, json: dict) -> httpx.Response:
    return httpx.post(url, headers=_supabase_storage_headers(), json=json, timeout=10)


def _supabase_storage_headers() -> dict[str, str]:
    return {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
    }
