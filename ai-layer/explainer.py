"""
Selects a model, renders prompts, calls the model, and parses the response.
Rule of thumb: use K2-Think for multi-element conflicts, Gemma for simple ones.
"""
from jinja2 import Environment, FileSystemLoader
from models.k2_think_client import k2_think_complete
import pathlib

_env = Environment(loader=FileSystemLoader(pathlib.Path(__file__).parent / "prompts"))


def _render(template_name: str, variables: dict) -> str:
    return _env.get_template(template_name).render(**variables)


async def explain_conflict(raw: dict) -> dict:
    context = raw.get("context", {})
    reason = raw.get("reason_code", "")

    prompt = _render("conflict_explanation.j2", {
        "reason_code": reason,
        "elements": raw.get("elements", []),
        **context,
    })
    plain_english = await k2_think_complete(prompt)

    suggestion_prompt = _render("resolution_suggestion.j2", {
        "plain_english": plain_english,
        "reason_code": reason,
        **context,
    })
    suggestion = await k2_think_complete(suggestion_prompt)

    return {"plain_english": plain_english, "suggestion": suggestion}
