from typing import List, Dict

import httpx


class OpenAICompatProvider:
    """Unified provider for any OpenAI-compatible /v1/chat/completions endpoint."""

    def __init__(
        self,
        endpoint: str,
        model_id: str,
        api_key: str | None = None,
        is_local: bool = False,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.model_id = model_id
        self.api_key = api_key
        self.is_local = is_local

    def call(
        self,
        messages: List[Dict[str, str]],
        timeout: float = 60.0,
    ) -> str:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key and not self.is_local:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_id,
            "messages": messages,
        }

        resp = httpx.post(
            f"{self.endpoint}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
