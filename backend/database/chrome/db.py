from __future__ import annotations

import asyncio
import datetime
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import uuid4

from backend.project_config import settings

try:
    import chromadb
    from chromadb.api.models import Collection
except ImportError:
    chromadb = None
    Collection = None

logger = logging.getLogger(__name__)

@dataclass
class MemoryPayload:
    id: str
    agent_id: str
    description: str
    emotion: Optional[str]
    timestamp: datetime.datetime
    def as_response(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "emotion": self.emotion,
            "timestamp": self.timestamp.isoformat(),
        }

class _FallbackMemoryStore:
    """
    Простейшее in-memory хранилище, используется если chromadb недоступен.
    """
    def __init__(self) -> None:
        self._items: Dict[str, MemoryPayload] = {}
    def add(self, agent_id: str, description: str, emotion: Optional[str]) -> MemoryPayload:
        item = MemoryPayload(
            id=str(uuid4()),
            agent_id=agent_id,
            description=description,
            emotion=emotion,
            timestamp=datetime.datetime.utcnow(),
        )
        self._items[item.id] = item
        return item
    def list_for_agent(self, agent_id: str, limit: int = 20) -> List[MemoryPayload]:
        items = [m for m in self._items.values() if m.agent_id == agent_id]
        return sorted(items, key=lambda m: m.timestamp)[-limit:]

class ChromaMemoryStore:
    """
    Обертка над облачным ChromaDB CloudClient с fallback на memory
    """
    def __init__(self) -> None:
        self._fallback = _FallbackMemoryStore()
        self._collection: Optional[Any] = None

        if chromadb is None:
            logger.warning("chromadb не установлен; используется in-memory store")
            return
        try:
            # Проверяем, заданы ли параметры для подключения к облаку
            if settings.CHROMA_API_KEY and settings.CHROMA_TENANT and settings.CHROMA_DB_NAME:
                logger.info("Using ChromaDB Cloud...")
                # Подключение к Chroma Cloud
                self._client = chromadb.CloudClient(
                    api_key=settings.CHROMA_API_KEY,
                    tenant=settings.CHROMA_TENANT,
                    database=settings.CHROMA_DB_NAME
                )
                self._collection = self._client.get_or_create_collection(
                    name="memories",
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info("Chroma Cloud collection ready: %s", "memories")
            else:
                logger.info("ChromaDB Cloud credentials not provided, skipping cloud initialization.")
                self._collection = None
        except Exception as exc:
            logger.error("Не удалось подключиться к Chroma Cloud, fallback. %s", exc)
            self._collection = None

    async def add_memory(self, agent_id: str, description: str, emotion: Optional[str]) -> MemoryPayload:
        if not description:
            raise ValueError("memory description is required")
        if self._collection is None:
            return self._fallback.add(agent_id, description, emotion)
        memory_id = str(uuid4())
        timestamp = datetime.datetime.utcnow()
        metadata = {
            "agent_id": agent_id,
            "emotion": emotion,
            "timestamp": timestamp.isoformat(),
        }
        try:
            await asyncio.to_thread(
                self._collection.upsert,
                ids=[memory_id],
                documents=[description],
                metadatas=[metadata],
            )
        except Exception as exc:
            logger.error("Chroma upsert failed, fallback to memory cache: %s", exc)
            return self._fallback.add(agent_id, description, emotion)
        return MemoryPayload(
            id=memory_id,
            agent_id=agent_id,
            description=description,
            emotion=emotion,
            timestamp=timestamp,
        )

    async def fetch_agent_memories(self, agent_id: str, limit: int = 20) -> List[MemoryPayload]:
        if self._collection is None:
            return self._fallback.list_for_agent(agent_id, limit)
        try:
            result = await asyncio.to_thread(
                self._collection.get,
                where={"agent_id": agent_id},
                limit=limit,
                include=["metadatas", "documents"],
            )
            items: List[MemoryPayload] = []
            ids = result.get("ids") or []
            docs = result.get("documents") or []
            metadatas = result.get("metadatas") or []
            for idx, mid in enumerate(ids):
                meta = metadatas[idx] if idx < len(metadatas) else {}
                doc = docs[idx] if idx < len(docs) else ""
                ts_raw = meta.get("timestamp")
                try:
                    ts = (
                        datetime.datetime.fromisoformat(ts_raw)
                        if ts_raw
                        else datetime.datetime.utcnow()
                    )
                except Exception:
                    ts = datetime.datetime.utcnow()
                items.append(
                    MemoryPayload(
                        id=mid,
                        agent_id=str(meta.get("agent_id") or agent_id),
                        description=doc,
                        emotion=meta.get("emotion"),
                        timestamp=ts,
                    )
                )
            return sorted(items, key=lambda m: m.timestamp)[-limit:]
        except Exception as exc:
            logger.error("Chroma fetch failed, fallback: %s", exc)
            return self._fallback.list_for_agent(agent_id, limit)

    async def delete_agent_memories(self, agent_id: str) -> None:
        """
        Удалить все воспоминания агента из ChromaDB.
        """
        if self._collection is None:
            # Для fallback просто очищаем из памяти
            self._fallback._items = {
                k: v for k, v in self._fallback._items.items() if v.agent_id != agent_id
            }
            return
        try:
            # Получаем все ID воспоминаний агента
            result = await asyncio.to_thread(
                self._collection.get,
                where={"agent_id": agent_id},
                include=["metadatas"],
            )
            ids_to_delete = result.get("ids") or []
            if ids_to_delete:
                await asyncio.to_thread(
                    self._collection.delete,
                    ids=ids_to_delete,
                )
                logger.info("Удалено %d воспоминаний агента %s из ChromaDB", len(ids_to_delete), agent_id)
        except Exception as exc:
            logger.error("Ошибка при удалении воспоминаний из ChromaDB: %s", exc)

memory_store = ChromaMemoryStore()
