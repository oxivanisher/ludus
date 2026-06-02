from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from core.config import settings
from core.push import delete_subscription, save_subscription

router = APIRouter(prefix="/api/push")


class PushSubscriptionBody(BaseModel):
    subscription: dict  # the full PushSubscription JSON from the browser


def _require_token(x_player_token: str | None) -> str:
    if not x_player_token:
        raise HTTPException(status_code=401, detail="X-Player-Token header required")
    return x_player_token


@router.get("/vapid-public-key")
async def vapid_public_key():
    """Return the VAPID public key so the browser can subscribe."""
    if not settings.vapid_public_key:
        raise HTTPException(status_code=501, detail="Push notifications not configured")
    return {"publicKey": settings.vapid_public_key}


@router.post("/subscribe", status_code=204)
async def subscribe(
    body: PushSubscriptionBody,
    x_player_token: str | None = Header(default=None),
):
    token = _require_token(x_player_token)
    await save_subscription(token, body.subscription)


@router.delete("/subscribe", status_code=204)
async def unsubscribe(
    body: PushSubscriptionBody,
    x_player_token: str | None = Header(default=None),
):
    token = _require_token(x_player_token)
    await delete_subscription(token, body.subscription)
