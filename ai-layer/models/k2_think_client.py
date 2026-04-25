"""
K2-Think-v2 (MBZUAI-IFM/K2-Think-v2) via api.k2think.ai.
OpenAI-compatible endpoint — uses the openai SDK pointed at the K2 base URL.

Get your API key at https://api.k2think.ai
Set K2_API_KEY in your .env before running.
"""
import os
import re
from openai import AsyncOpenAI

_client = AsyncOpenAI(
    api_key=os.environ["K2_API_KEY"],
    base_url=os.getenv("K2_BASE_URL", "https://api.k2think.ai/v1"),
)

K2_MODEL = os.getenv("K2_MODEL", "MBZUAI-IFM/K2-Think-v2")


async def k2_think_complete(prompt: str) -> str:
    response = await _client.chat.completions.create(
        model=K2_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=512,
        # K2-Think-v2 streams by default in the docs; we disable it here for simplicity.
        stream=False,
    )
    raw = response.choices[0].message.content.strip()
    # K2-Think emits a <think>…</think> block before its final answer — strip it.
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    return raw
