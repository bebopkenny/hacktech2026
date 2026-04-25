# ai-layer — Person 4

Pure Python FastAPI service. Receives a `RawConflict` from the coordination service and returns plain-English `plain_english` + `suggestion` fields using Gemma 4 and/or K2-Think-V2.

## Files

| File | Purpose |
|---|---|
| `main.py` | FastAPI app — single `POST /explain` endpoint |
| `models.py` | Re-exports `RawConflict` / `EnrichedConflict` from coordination-service (or duplicates them) |
| `explainer.py` | Orchestrates model selection + prompt rendering + response parsing |
| `prompts/conflict_explanation.j2` | Jinja2 template for the main conflict → plain English prompt |
| `prompts/resolution_suggestion.j2` | Jinja2 template for the suggestion sub-prompt |
| `models/gemma_client.py` | Thin wrapper around the Gemma 4 inference endpoint |
| `models/k2_think_client.py` | Thin wrapper around the K2-Think-V2 inference endpoint |
| `sample_conflicts/` | JSON fixtures for testing without the coordination service |

## Running locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

Test with a sample conflict:
```bash
curl -X POST http://localhost:8001/explain \
  -H "Content-Type: application/json" \
  -d @sample_conflicts/host_modified.json
```

## Models

| Model | Provider | When used |
|---|---|---|
| `MBZUAI-IFM/K2-Think-v2` | [api.k2think.ai](https://api.k2think.ai) | Multi-element conflicts — uses chain-of-thought reasoning |
| `gemma3:27b` | Ollama on Vultr GPU | Single-element fast warnings |

**K2-Think-v2** is called via `https://api.k2think.ai/v1` (OpenAI-compatible). Set `K2_API_KEY` in `.env`.

**Gemma** runs on Ollama on the same Vultr GPU instance. No API key needed. Install with `setup.sh`, then `ollama pull gemma3:27b`. Swap to `gemma3:4b` on smaller instances.

## Prompt design

Each prompt template receives the full `RawConflict.context` dict as variables. Keep templates in separate `.j2` files so they can be tweaked without touching Python. Version control the templates — prompt changes should be reviewable diffs.

## Adding a new conflict type

1. Add a case to `prompts/conflict_explanation.j2` with a recognizable `reason_code`.
2. Write a sample conflict JSON in `sample_conflicts/`.
3. Test with `curl` before wiring into the coordination service.
