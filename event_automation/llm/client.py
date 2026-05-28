"""LLM API client supporting OpenAI/Anthropic."""
import logging
import os
from typing import Optional

from event_automation.config import config

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM API client supporting OpenAI and Anthropic."""

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        provider: str = None,
    ):
        """
        Initialize LLMClient.

        Args:
            api_key: API key (defaults to config.LLM_API_KEY)
            model: Model name (defaults to config.LLM_MODEL)
            provider: "openai" or "anthropic" (auto-detected from model if None)
        """
        self.api_key = api_key or config.LLM_API_KEY
        self.model = model or config.LLM_MODEL
        self.provider = provider or config.LLM_PROVIDER

        self._client = None
        self._call_count = 0
        self._total_tokens = 0

    @property
    def client(self):
        """Lazy-load the appropriate client."""
        if self._client is None:
            if self.provider == "anthropic":
                try:
                    from anthropic import AsyncAnthropic
                    self._client = AsyncAnthropic(api_key=self.api_key)
                except ImportError:
                    raise ImportError("anthropic package not installed")
            else:
                try:
                    from openai import AsyncOpenAI
                    self._client = AsyncOpenAI(api_key=self.api_key)
                except ImportError:
                    raise ImportError("openai package not installed")

        return self._client

    async def complete(self, prompt: str, system_prompt: str = None) -> str:
        """
        Make an LLM completion call.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)

        Returns:
            LLM response text
        """
        self._call_count += 1

        if self.provider == "anthropic":
            return await self._complete_anthropic(prompt, system_prompt)
        else:
            return await self._complete_openai(prompt, system_prompt)

    async def _complete_openai(self, prompt: str, system_prompt: str = None) -> str:
        """Make OpenAI completion call."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
            )

            self._total_tokens += response.usage.total_tokens if hasattr(response, "usage") else 0

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    async def _complete_anthropic(self, prompt: str, system_prompt: str = None) -> str:
        """Make Anthropic completion call."""
        kwargs = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            response = await self.client.messages.create(**kwargs)

            self._total_tokens += response.usage.input_tokens + response.usage.output_tokens

            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise

    @property
    def call_count(self) -> int:
        """Get number of LLM calls made."""
        return self._call_count

    @property
    def total_tokens(self) -> int:
        """Get total tokens used."""
        return self._total_tokens

    def reset_stats(self) -> None:
        """Reset call count and token tracking."""
        self._call_count = 0
        self._total_tokens = 0