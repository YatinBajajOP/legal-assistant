"""Batched OpenAI embedding generation."""
from __future__ import annotations

import asyncio
from typing import List

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

from app.core.config import settings

_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(5))
async def _embed_batch(texts: List[str]) -> List[List[float]]:
    response = await _client.embeddings.create(model=settings.EMBEDDING_MODEL, input=texts)
    # The API preserves input order in `data`.
    return [item.embedding for item in response.data]


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts, batching requests and running batches concurrently."""
    if not texts:
        return []

    batch_size = settings.EMBEDDING_BATCH_SIZE
    batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]

    semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_EMBEDDING_BATCHES)

    async def run_batch(batch: List[str]) -> List[List[float]]:
        async with semaphore:
            return await _embed_batch(batch)

    results = await asyncio.gather(*(run_batch(batch) for batch in batches))
    embeddings: List[List[float]] = []
    for result in results:
        embeddings.extend(result)
    return embeddings


async def embed_query(text: str) -> List[float]:
    embeddings = await _embed_batch([text])
    return embeddings[0]
