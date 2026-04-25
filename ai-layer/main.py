"""
AI layer entry point.
POST /explain — receives a RawConflict JSON, returns { plain_english, suggestion }.
"""
import pathlib

# Load .env for local dev (no-op if python-dotenv isn't installed or file missing).
try:
    from dotenv import load_dotenv
    load_dotenv(pathlib.Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from explainer import explain_conflict

app = FastAPI(title="RevitSync AI Layer")


class RawConflictRequest(BaseModel):
    conflict_id: str
    severity: str
    elements: list[int]
    reason_code: str
    context: dict


class ExplainResponse(BaseModel):
    plain_english: str
    suggestion: str


@app.post("/explain", response_model=ExplainResponse)
async def explain(req: RawConflictRequest):
    try:
        result = await explain_conflict(req.model_dump())
        return ExplainResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
