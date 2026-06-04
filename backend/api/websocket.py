import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from core import connections
from core import session as session_store
from models.schemas import SessionResponse

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

    player_token: str | None = token
    if player_token:
        connections.register(session_id, player_token, websocket)

    try:
        # Send initial state — my_username is correct immediately because we
        # have the token from the query parameter.
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
                            updated = await session_store.apply_action(
                                session_id, session_store.COMPUTER_TOKEN, computer_action
                            )
                            for tok, ws in connections.get_sockets(session_id).items():
                                response = SessionResponse.from_session(updated, tok)
                                await _send(ws, {"type": "state", "session": response.model_dump()})
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
