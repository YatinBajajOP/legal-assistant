"""Chat-completion wrapper used to answer grouped resolution-plan questions."""
from __future__ import annotations

import json
from typing import Any, Dict

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

from app.core.config import settings

_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(settings.LLM_MAX_RETRIES))
async def complete_json(*, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """Call the chat model and parse a JSON object response."""
    response = await _client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)
