"""Spectator endpoints - public access, no auth required."""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from request_trace import RouteWithLogging

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["spectator"],
    route_class=RouteWithLogging,
)


def _get_engine():
    from main import game_engine
    return game_engine


def _get_ws_manager():
    from main import ws_manager
    return ws_manager


@router.websocket("/ws/spectator")
async def spectator_websocket(websocket: WebSocket):
    """WebSocket endpoint for spectator live feed."""
    manager = _get_ws_manager()
    if manager is None:
        await websocket.close(code=1011, reason="WebSocket manager not initialized")
        return

    await manager.connect(websocket)
    logger.info(f"Spectator connected: {websocket.client}")

    try:
        # Send initial state
        engine = _get_engine()
        if engine:
            status = engine.table.get_status()
            await websocket.send_json({
                "type": "initial_state",
                "table_status": status.model_dump(mode="json"),
                "leaderboard": [e.model_dump(mode="json") for e in engine.get_leaderboard()],
            })
            logger.info(f"Sent initial state to spectator: {websocket.client}")

        # Keep connection alive - wait for disconnect
        while True:
            # We don't expect messages from spectators, but we need to keep the connection alive
            # and detect disconnects
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                logger.info(f"Spectator disconnected: {websocket.client}")
                break
    except Exception as e:
        logger.error(f"WebSocket error for {websocket.client}: {e}", exc_info=True)
    finally:
        manager.disconnect(websocket)


@router.get("/api/v1/spectator/leaderboard")
async def get_leaderboard():
    """Get the bot leaderboard (public, no auth)."""
    engine = _get_engine()
    if engine is None:
        return {"leaderboard": [], "count": 0}

    entries = engine.get_leaderboard()
    logger.info(f"Leaderboard retrieved: {len(entries)} entries")
    return {
        "leaderboard": [e.model_dump() for e in entries],
        "count": len(entries),
    }


@router.get("/api/v1/spectator/table/{table_id}/status")
async def spectator_table_status(table_id: str):
    """Get table status (public, no auth)."""
    engine = _get_engine()
    if engine is None:
        return {"error": "Game engine not initialized"}

    status = engine.table.get_status()
    logger.info(f"Spectator retrieved table {table_id} status: phase={status.phase.value}, bots={status.bot_count}")
    return status.model_dump()
