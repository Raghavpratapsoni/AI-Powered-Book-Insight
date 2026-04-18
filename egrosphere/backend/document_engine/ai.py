import hashlib

from django.conf import settings
from django.core.cache import cache
from openai import OpenAI


class LLMClient:
    def __init__(self):
        base_url = settings.LLM_BASE_URL.rstrip('/')
        api_key = settings.OPENAI_API_KEY.strip()

        self.model = settings.LLM_MODEL
        self.provider = 'disabled'
        self.client = None

        if base_url:
            self.provider = 'lmstudio'
            self.client = OpenAI(
                base_url=base_url,
                api_key=api_key or 'lm-studio',
            )
        elif api_key:
            self.provider = 'openai'
            self.client = OpenAI(api_key=api_key)

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def chat(self, system_prompt: str, user_prompt: str, *, max_tokens: int = 300, temperature: float = 0.2, cache_namespace: str = '') -> str | None:
        if not self.enabled:
            return None

        cache_key = ''
        if cache_namespace:
            cache_key = self._cache_key(cache_namespace, system_prompt, user_prompt, max_tokens, temperature)
            cached = cache.get(cache_key)
            if cached:
                return cached

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = (response.choices[0].message.content or '').strip()

        if cache_key and content:
            cache.set(cache_key, content, timeout=settings.AI_CACHE_TIMEOUT)
        return content or None

    def _cache_key(self, namespace: str, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> str:
        payload = '|'.join(
            [
                self.provider,
                self.model,
                str(max_tokens),
                str(temperature),
                system_prompt,
                user_prompt,
            ]
        )
        digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        return f'{namespace}:{digest}'
