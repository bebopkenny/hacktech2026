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
        max_tokens=1024,
        stream=False,
    )
    raw = response.choices[0].message.content.strip()

    # K2-Think emits reasoning before its final answer.
    # Strip <think>…</think> blocks (tagged form).
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    # Handle responses that close with </think> but no opening tag.
    if "</think>" in raw:
        raw = raw.split("</think>")[-1].strip()

    # K2 reasons with quoted candidates like "Ask James to reposition the beam."
    # Extract the last clean quoted "Ask X to Y" sentence — the most considered option.
    candidates = re.findall(r'"(Ask \w[\w\s\'\-]+ to [^"]{5,})"', raw)
    candidates = [c for c in candidates if "___" not in c and len(c.split()) <= 30]
    if candidates:
        return candidates[-1].strip(".")  + "."

    # Fallback: first non-empty line after stripping.
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    return lines[0] if lines else raw
