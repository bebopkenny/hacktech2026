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

_SYSTEM = (
    "You are a BIM coordination assistant. "
    "Respond with only the final answer — one sentence, no thinking, no reasoning, no preamble."
)


async def k2_think_complete(prompt: str) -> str:
    response = await _client.chat.completions.create(
        model=K2_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=256,
        stream=False,
    )
    raw = response.choices[0].message.content.strip()
    # K2-Think may wrap reasoning in <think>…</think> or close with </think> (no opening tag).
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    if "</think>" in raw:
        raw = raw.split("</think>")[-1].strip()
    # Take only the first non-empty line — guard against any trailing reasoning.
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    return lines[0] if lines else raw
