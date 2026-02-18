import asyncio
import logging
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class EventBroker:
    """
    Простая брокер-шина для рассылки событий по WebSocket.

    Хранит множество активных WebSocket-подключений и позволяет
    отправлять одно и то же событие всем подписчикам.
    """

    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """
        Зарегистрировать новое WebSocket-подключение.
        """
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info("Установлено WebSocket-подключение; всего подключений=%d", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Удалить WebSocket-подключение из списка активных.
        """
        async with self._lock:
            self._connections.discard(websocket)
        logger.info("WebSocket-подключение закрыто; всего подключений=%d", len(self._connections))

    async def broadcast(self, payload: Dict) -> None:
        """
        Отправить событие всем активным WebSocket-подключениям.

        Если отправка на конкретный сокет падает, соединение
        помечается как закрытое и удаляется.
        """
        async with self._lock:
            targets = list(self._connections)

        if not targets:
            logger.debug("Рассылка по WebSocket пропущена: нет активных подключений")
            return

        logger.debug("Рассылка события по WebSocket: type=%s, получателей=%d", payload.get("type"), len(targets))
        for ws in targets:
            try:
                await ws.send_json(payload)
            except Exception as exc:
                logger.warning("Ошибка отправки по WebSocket, отключаем клиента: %s", exc)
                await self.disconnect(ws)


broker = EventBroker()


