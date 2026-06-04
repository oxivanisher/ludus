import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from core import connections
from core import session as session_store
from models.schemas import SessionResponse

logger = logging.getLogger("ludus.ws")
router = APIRouter()


async def _send(ws: WebSocket, payload: dict) -> bool:
    try:
        await ws.send_text(json.dumps(payload))
        return True
    except Exception:
        return False


async def _broadcast(session_id: str, payload: dict, exclude_token: str | None = None) -> None:
    dead_tokens = []
    for token, ws in connections.get_sockets(session_id).items():
        if token == exclude_token:
            continue
        ok = await _send(ws, payload)
        if not ok:
            dead_tokens.append(token)
    for token in dead_tokens:
        connections.unregister(session_id, token)


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str | None = Query(default=None),
):
    await websocket.accept()

    session = await session_store.get_session(session_id)
    if session is None:
        await _send(websocket, {"type": "error", "message": "Session not found"})
        await websocket.close()
        return

    # Block external clients from impersonating the computer
    if token == session_store.COMPUTER_TOKEN:
        await _send(websocket, {"type": "error", "message": "Forbidden"})
        await websocket.close()
        return

    player_token: str | None = token

    try:
        # When no token in query, require an "identify" message as the first
        # frame so the token is never written to server access logs via the URL.
        if not player_token:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _send(websocket, {"type": "error", "message": "Invalid JSON"})
                await websocket.close()
                return

            if msg.get("type") == "identify":
                candidate = msg.get("token") or None
                if candidate == session_store.COMPUTER_TOKEN:
                    await _send(websocket, {"type": "error", "message": "Forbidden"})
                    await websocket.close()
                    return
                player_token = candidate
                # Refresh session state — it may have changed while we waited
                session = await session_store.get_session(session_id) or session
            else:
                await _send(websocket, {"type": "error", "message": "Expected identify message"})
                await websocket.close()
                return

        if player_token:
            connections.register(session_id, player_token, websocket)

        await _send(
            websocket,
            {"type": "state", "session": SessionResponse.from_session(session, player_token).model_dump()},
        )

        async for raw in _iter_ws(websocket):
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _send(websocket, {"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type")

            if msg_type == "action":
                if not player_token:
                    await _send(websocket, {"type": "error", "message": "No player token provided"})
                    continue
                try:
                    updated = await session_store.apply_action(
                        session_id, player_token, msg.get("action", {})
                    )
                    # Broadcast personalised state to every connected player
                    for tok, ws in connections.get_sockets(session_id).items():
                        response = SessionResponse.from_session(updated, tok)
                        await _send(ws, {"type": "state", "session": response.model_dump()})

                    # If it's now the computer's turn, apply its action(s) in a loop
                    # (loop handles bonus turns, e.g. Mancala landing on own store)
                    if updated.get("vs_computer") and updated.get("status") == "playing":
                        from core.plugin_loader import get_game
                        game_plugin = get_game(updated["game_slug"])
                        safety = 0
                        while (safety < 20
                               and game_plugin
                               and updated.get("status") == "playing"
                               and updated.get("current_turn") == session_store.COMPUTER_USERNAME):
                            safety += 1
                            computer_action = game_plugin.get_computer_action(
                                updated["state"], session_store.COMPUTER_USERNAME
                            )
                            if not computer_action:
                                break
                            try:
                                updated = await session_store.apply_action(
                                    session_id, session_store.COMPUTER_TOKEN, computer_action
                                )
                            except ValueError as computer_err:
                                logger.error(
                                    "Computer action failed in session %s: %s",
                                    session_id, computer_err,
                                )
                                break
                            for tok, ws in connections.get_sockets(session_id).items():
                                response = SessionResponse.from_session(updated, tok)
                                await _send(ws, {"type": "state", "session": response.model_dump()})

                        # Recovery: if the computer is still to play, forfeit it
                        # so the human isn't left with a permanently stuck game
                        if (updated.get("status") == "playing" and
                                updated.get("current_turn") == session_store.COMPUTER_USERNAME):
                            logger.error(
                                "Computer stuck in session %s (safety=%d); forfeiting to human",
                                session_id, safety,
                            )
                            try:
                                updated = await session_store.forfeit_session(
                                    session_id, session_store.COMPUTER_TOKEN
                                )
                                for tok, ws in connections.get_sockets(session_id).items():
                                    response = SessionResponse.from_session(updated, tok)
                                    await _send(ws, {"type": "state", "session": response.model_dump()})
                            except Exception as recover_err:
                                logger.error(
                                    "Could not recover stuck session %s: %s",
                                    session_id, recover_err,
                                )

                except ValueError as e:
                    await _send(websocket, {"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        pass
    finally:
        if player_token:
            connections.unregister(session_id, player_token)


async def _iter_ws(ws: WebSocket):
    while True:
        try:
            yield await ws.receive_text()
        except WebSocketDisconnect:
            return
