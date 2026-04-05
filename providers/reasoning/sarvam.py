"""Sarvam AI reasoning provider using the official sarvamai SDK."""

import json
import logging
import re
from typing import Optional, Dict

from ..base import ReasoningProvider, ProviderResponse, timed_call

logger = logging.getLogger(__name__)


class SarvamReasoningProvider(ReasoningProvider):
    """Uses Sarvam AI chat completions for maternal-health reasoning.

    Accepts a pre-initialized sarvamai.SarvamAI client from the factory
    so all Sarvam providers share one authenticated session.
    """

    def __init__(self, client, model: str = "sarvam-m"):
        self._client = client
        self._model = model

    @staticmethod
    def _strip_think_tags(text: str) -> str:
        """Remove <think>...</think> reasoning traces from model output."""
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    @timed_call
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> ProviderResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            choice = response.choices[0]
            content = choice.message.content
            content = self._strip_think_tags(content)
            usage = getattr(response, "usage", None)
            return ProviderResponse(
                result=content,
                provider_name="sarvam_reasoning",
                model_name=self._model,
                input_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
                output_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
                metadata={"model": self._model},
            )
        except Exception as e:
            logger.error(f"Sarvam reasoning failed: {e}")
            from .mock import MockReasoningProvider
            return MockReasoningProvider().generate(prompt, system_prompt, temperature, max_tokens)

    @timed_call
    def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        response_schema: Optional[Dict] = None,
    ) -> ProviderResponse:
        schema_instruction = ""
        if response_schema:
            schema_instruction = (
                f"\n\nRespond ONLY with valid JSON matching this schema:\n"
                f"{json.dumps(response_schema, indent=2)}"
            )

        result = self.generate(
            prompt=prompt + schema_instruction,
            system_prompt=system_prompt + "\nYou must respond with valid JSON only.",
            temperature=0.1,
        )
        try:
            parsed = json.loads(result.result)
            result.result = parsed
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to parse structured response, returning raw")
        return result
