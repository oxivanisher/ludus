"""
Web Push notification dispatch.

Subscriptions are stored in Redis under player:{token}:push_subs as a
Redis SET of JSON-encoded PushSubscription objects.  When it is a player's
turn we send a push to every subscription they have registered, skipping
delivery when they already have an active WebSocket open on that session.
"""

import json
import logging

from pywebpush import WebPushException, webpush

from .config import settings
from .connections import is_connected
from .redis_client import get_redis

logger = logging.getLogger(__name__)

PUSH_SUBS_TTL = 90 * 86400  # keep subscriptions for 90 days


async def save_subscription(player_token: str, subscription: dict) -> None:
    r = await get_redis()
    key = f"player:{player_token}:push_subs"
    await r.sadd(key, json.dumps(subscription, sort_keys=True))
    await r.expire(key, PUSH_SUBS_TTL)


async def delete_subscription(player_token: str, subscription: dict) -> None:
    r = await get_redis()
    key = f"player:{player_token}:push_subs"
    await r.srem(key, json.dumps(subscription, sort_keys=True))


async def _get_subscriptions(player_token: str) -> list[dict]:
    r = await get_redis()
    raw = await r.smembers(f"player:{player_token}:push_subs")
    return [json.loads(s) for s in raw]


async def notify_player(
    *,
    session_id: str,
    player_token: str,
    game_name: str,
) -> None:
    """
    Send a 'your turn' push to the given player unless they currently have
    an active WebSocket connection on this session.
    """
    if not settings.vapid_private_key:
        return  # push not configured

    if is_connected(session_id, player_token):
        return  # player is already watching — no need to interrupt

    subscriptions = await _get_subscriptions(player_token)
    if not subscriptions:
        return

    payload = json.dumps(
        {
            "title": "Ludus — Your turn!",
            "body": f"It's your turn in {game_name}.",
            "url": f"/game/{session_id}",
        }
    )

    stale: list[dict] = []
    for sub in subscriptions:
        try:
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={
                    "sub": f"mailto:{settings.vapid_contact_email}",
                },
            )
        except WebPushException as e:
            if e.response is not None and e.response.status_code == 410:
                stale.append(sub)
            else:
                logger.warning("Push failed for token %s: %s", player_token[:8], e)

    for sub in stale:
        await delete_subscription(player_token, sub)
