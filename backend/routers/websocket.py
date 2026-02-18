# ---------------------------------------------------------
# Роутер для WebSocket соединений
# ---------------------------------------------------------

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.realtime import broker

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket) -> None:
    """
    WS поток для событий/уведомлений (лента событий, обновления агентов).
    """
    await broker.connect(websocket)
    try:
        while True:
            # Эхо/пинг-понг для поддержания соединения
            await websocket.receive_text()
    except WebSocketDisconnect:
        await broker.disconnect(websocket)
    except Exception:
        await broker.disconnect(websocket)
