from fastapi import APIRouter, Header, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from core.config import settings

router = APIRouter()


@router.get("/metrics", include_in_schema=False)
async def prometheus_metrics(authorization: str | None = Header(default=None)):
    if not settings.metrics_token:
        raise HTTPException(status_code=404)
    if authorization != f"Bearer {settings.metrics_token}":
        raise HTTPException(
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Invalid or missing token",
        )
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
