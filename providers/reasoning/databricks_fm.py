"""Databricks Foundation Model API reasoning provider."""

import json
import logging
import os
from typing import Optional, Dict

from ..base import ReasoningProvider, ProviderResponse, timed_call

logger = logging.getLogger(__name__)


class DatabricksReasoningProvider(ReasoningProvider):
    """Uses Databricks Foundation Model API for LLM reasoning."""

    def __init__(self, model: str = "databricks-meta-llama-3-1-70b-instruct"):
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from databricks.sdk import WorkspaceClient
                self._client = WorkspaceClient()
            except Exception as e:
                logger.error(f"Failed to init Databricks client: {e}")
                raise
        return self._client

    @timed_call
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> ProviderResponse:
        try:
            client = self._get_client()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.serving_endpoints.query(
                name=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            return ProviderResponse(
                result=content,
                provider_name="databricks_fm",
                model_name=self.model,
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
            )
        except Exception as e:
            logger.error(f"Databricks FM API failed: {e}, falling back to mock")
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
            schema_instruction = f"\n\nRespond with valid JSON matching: {json.dumps(response_schema)}"

        result = self.generate(
            prompt=prompt + schema_instruction,
            system_prompt=system_prompt + "\nRespond with valid JSON only.",
            temperature=0.1,
        )
        try:
            parsed = json.loads(result.result)
            result.result = parsed
        except (json.JSONDecodeError, TypeError):
            pass
        return result
