"""
Gemma via Ollama running on the Vultr GPU instance.
Ollama exposes an OpenAI-compatible endpoint at /v1, so we use the same SDK as K2.

On the Vultr VM, Ollama is installed by setup.sh and the model is pre-pulled.
For local dev without a GPU, swap GEMMA_BASE_URL to a Colab or any hosted Gemma endpoint.
"""
import os
from openai import AsyncOpenAI

_client = AsyncOpenAI(
    api_key="ollama",  # Ollama doesn't need a real key; this satisfies the SDK validator.
    base_url=os.getenv("GEMMA_BASE_URL", "http://localhost:11434/v1"),
)

GEMMA_MODEL = os.getenv("GEMMA_MODEL", "gemma3:27b")


async def gemma_complete(prompt: str) -> str:
    response = await _client.chat.completions.create(
        model=GEMMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=128,
    )
    return response.choices[0].message.content.strip()
