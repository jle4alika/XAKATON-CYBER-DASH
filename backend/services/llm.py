from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, List, Optional

from openai import AsyncOpenAI
from openai._exceptions import RateLimitError
from backend.project_config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_ACTION = """Ты — симулятор действий конкретного агента в кибер-городе.
ВАЖНО: Отвечай ТОЛЬКО на русском языке, одной строкой, лаконично, без цитат, без разметки.
Не добавляй время и имена других агентов, только действие. Используй только русский язык.

Тебе всегда передают информацию об агенте: его имя, настроение, уровень энергии,
текущую задачу, недавние воспоминания и текстовое описание персонажа.
Действия должны логично соответствовать именно ЭТОМУ агенту и его состоянию.

Будь креативным и разнообразным. Действия должны отражать личность агента и его текущее состояние.
Примеры: "осмотрел окрестности", "проверил систему безопасности", "изучил карту местности",
"нашел интересный артефакт", "проанализировал данные", "записал наблюдения в журнал".
"""

SYSTEM_PROMPT_CHAT = """Ты — конкретный AI-агент в виртуальном кибер-городе с уникальной личностью и взглядами.
ВАЖНО: Все твои сообщения должны быть ТОЛЬКО на русском языке. Никаких английских слов или фраз.

Ты общаешься с другим агентом в текстовом групповом чате.
Название и описание чата, а также подсказка "Тема: ..." всегда задают СИТУАЦИЮ, в которой вы находитесь.
Твои реплики должны строго соответствовать этой ситуации и развивать её, как будто вы уже находитесь внутри неё.

Отдельными системными сообщениями тебе всегда передают информацию о тебе самом и собеседнике:
имена, настроение, черты характера, краткое текстовое описание персонажа (background и роль),
а также воспоминания и историю переписки. Обязательно учитывай всё это в своих ответах.

Пиши только реплики чата от первого лица, как обычное сообщение в мессенджере.
НЕ описывай свои физические действия и окружение (например, "осматривает окрестности", "идёт по улице" и т.п.).
НЕ используй повествование от третьего лица и не начинай фразы глаголами действия без явного говорения.

Обсуждай разные темы: технологии, философия, планы, наблюдения, события в городе, идеи, споры, размышления —
но всегда в рамках контекста чата.
У тебя есть своё мнение и взгляды, которые могут отличаться от собеседника.
Учитывай своё настроение, черты характера и отношения с собеседником.
Отвечай коротко (1-5 предложений), естественно, на русском языке.
Не повторяйся — каждый раз говори о чём-то новом или развивай тему по-своему.
"""


class LLMClient:
    """
    Обертка над AsyncOpenAI с таймаутом и обработкой rate limiting.
    """

    def __init__(self) -> None:
        self.enabled = bool(settings.OPENAI_API_KEY)
        if self.enabled:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
        else:
            self.client = None
            self.model = None

    async def _call_with_retry(self, func, *args, max_retries=3, base_delay=1.0, **kwargs):
        """
        Вызов функции с экспоненциальной задержкой при rate limit ошибках.
        """
        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except RateLimitError as e:
                if attempt == max_retries:
                    logger.warning(f"Превышено максимальное количество попыток после rate limit: {e}")
                    raise

                # Экспоненциальная задержка: base_delay * (2 ^ attempt) + случайная добавка
                delay = base_delay * (2 ** attempt) + (0.1 * attempt)
                logger.info(
                    f"Rate limit достигнут. Повтор через {delay:.2f} секунд (попытка {attempt + 1}/{max_retries + 1})")
                await asyncio.sleep(delay)
            except Exception as e:
                logger.warning(f"Неожиданная ошибка при вызове API: {e}")
                raise

    async def generate_action(
            self,
            agent_name: str,
            mood: float,
            energy: int,
            current_task: Optional[str],
            memories: List[str],
            traits: List[str] = None,
            persona: str | None = None,
            timeout: float = 4.0,
    ) -> Optional[str]:
        if not self.enabled:
            return None

        mood_str = f"{mood:.2f}"
        mem_text = "; ".join(memories[:5]) if memories else "нет свежих воспоминаний"
        task_text = current_task or "нет активной задачи"
        traits_text = ", ".join(traits[:3]) if traits else "обычный"
        persona_text = persona.strip() if isinstance(persona, str) else ""

        user_prompt = (
            f"Агент: {agent_name}\n"
            f"Черты характера: {traits_text}\n"
            f"{persona_text}"
            f"Настроение: {mood_str}\n"
            f"Энергия: {energy}\n"
            f"Текущая задача: {task_text}\n"
            f"Недавние воспоминания: {mem_text}\n"
            f"Сформулируй уникальное, интересное действие, которое отражает личность агента. "
            f"Будь разнообразным - не повторяй предыдущие действия. Только русский язык."
        )

        async def _make_request():
            return await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_ACTION},
                        {"role": "user", "content": user_prompt},
                    ],
                ),
                timeout=timeout,
            )

        try:
            resp = await self._call_with_retry(_make_request)
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"LLM generate_action failed: {e}")
            return None

    async def generate_message(
            self,
            sender_name: str,
            sender_mood: float,
            sender_traits: List[str],
            receiver_name: str,
            affinity: float,
            recent_memories: List[str],
            conversation_history: List[Dict[str, str]],
            sender_persona: str | None = None,
            receiver_traits: List[str] = None,
            topic_hint: str = "",
            timeout: float = 4.0,
    ) -> Optional[str]:
        if not self.enabled:
            return None

        messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT_CHAT}]
        for msg in conversation_history or []:
            role = "assistant" if msg.get("from") == sender_name else "user"
            messages.append({"role": role, "content": msg.get("text", "")})
        if topic_hint:
            messages.append({"role": "system", "content": f"Тема: {topic_hint}"})
        if recent_memories:
            mem_text = "; ".join(recent_memories[:5])
            messages.append({"role": "system", "content": f"Воспоминания: {mem_text}"})
        sender_text = ", ".join(sender_traits[:3]) if sender_traits else ""
        receiver_text = ", ".join(receiver_traits[:3]) if receiver_traits else ""
        persona_parts: List[str] = []
        if sender_persona:
            persona_parts.append(f"Описание персонажа: {sender_persona.strip()[:200]}")
        summary = (
                f"Отправитель: {sender_name} (Настроение: {sender_mood:.2f}, Черты: {sender_text}). "
                f"Получатель: {receiver_name} (Черты: {receiver_text}). "
                f"Близость: {affinity:.2f}. " + " ".join(persona_parts)
        )
        messages.append({"role": "system", "content": summary})

        async def _make_request():
            return await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                ),
                timeout=timeout,
            )

        try:
            resp = await self._call_with_retry(_make_request)
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"LLM generate_message failed: {e}")
            return None

    async def generate_chat(
            self,
            history: List[Dict[str, str]],
            memory: str,
    ) -> Optional[str]:
        if not self.enabled:
            return None

        async def _make_request():
            return await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_CHAT},
                    *(history or []),
                    {"role": "system", "content": f"Воспоминание: {memory}"},
                ],
            )

        try:
            resp = await self._call_with_retry(_make_request)
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"LLM generate_chat failed: {e}")
            return None

    def sync_generate_chat(self, history: List[Dict[str, str]], memory: str) -> Optional[str]:
        if not self.enabled:
            return None

        async def _make_request():
            return await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_CHAT},
                    *(history or []),
                    {"role": "system", "content": f"Воспоминание: {memory}"},
                ],
            )

        try:
            resp = asyncio.run(self._call_with_retry(_make_request))
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"LLM sync_generate_chat failed: {e}")
            return None


llm_client = LLMClient()
