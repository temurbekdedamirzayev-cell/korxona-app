"""Bir nechta bepul AI xizmatlari: biri limitga yetsa, keyingisiga o'tadi."""

import logging
import os
import time
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

# Limitga yetgan xizmat shuncha soniya chetlab o'tiladi
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "60"))


@dataclass
class Provider:
    name: str
    url: str
    api_key: str
    model: str
    blocked_until: float = 0.0

    @property
    def available(self) -> bool:
        return bool(self.api_key) and time.time() >= self.blocked_until


def load_providers() -> list[Provider]:
    """Tartib .env dagi PROVIDER_ORDER bo'yicha (kalit yo'qlari tashlab ketiladi)."""
    all_providers = {
        "gemini": Provider(
            name="gemini",
            url="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        ),
        "groq": Provider(
            name="groq",
            url="https://api.groq.com/openai/v1/chat/completions",
            api_key=os.getenv("GROQ_API_KEY", ""),
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        ),
        "openrouter": Provider(
            name="openrouter",
            url="https://openrouter.ai/api/v1/chat/completions",
            api_key=os.getenv("OPENROUTER_API_KEY", ""),
            model=os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"),
        ),
    }
    order = os.getenv("PROVIDER_ORDER", "gemini,groq,openrouter").split(",")
    providers = [all_providers[n.strip()] for n in order if n.strip() in all_providers]
    return [p for p in providers if p.api_key]


class AllProvidersFailed(Exception):
    pass


class ProviderPool:
    def __init__(self, providers: list[Provider], client: httpx.AsyncClient | None = None):
        if not providers:
            raise ValueError("Hech bo'lmaganda bitta AI API kaliti kerak (.env faylini tekshiring)")
        self.providers = providers
        self.client = client or httpx.AsyncClient(timeout=60)

    async def chat(self, messages: list[dict]) -> tuple[str, str]:
        """Javob matni va qaysi xizmat javob berganini qaytaradi."""
        for p in self.providers:
            if not p.available:
                continue
            try:
                resp = await self.client.post(
                    p.url,
                    headers={"Authorization": f"Bearer {p.api_key}"},
                    json={"model": p.model, "messages": messages},
                )
            except httpx.HTTPError as e:
                log.warning("%s: tarmoq xatosi: %s", p.name, e)
                continue

            if resp.status_code == 429:
                # Limit tugadi: bir muddat bu xizmatni chetlab o'tamiz
                p.blocked_until = time.time() + COOLDOWN_SECONDS
                log.warning("%s: limit tugadi, %ss kutiladi", p.name, COOLDOWN_SECONDS)
                continue
            if resp.status_code != 200:
                log.warning("%s: xato %s: %s", p.name, resp.status_code, resp.text[:200])
                continue

            try:
                text = resp.json()["choices"][0]["message"]["content"]
            except (ValueError, KeyError, IndexError, TypeError):
                log.warning("%s: noto'g'ri javob: %s", p.name, resp.text[:200])
                continue
            if text:
                return text, p.name

        raise AllProvidersFailed("Hamma xizmatlar band yoki limit tugagan")
