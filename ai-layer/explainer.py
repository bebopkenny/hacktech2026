"""
Generates conflict notifications and resolution suggestions.
plain_english: rendered directly from conflict_explanation.j2 (no AI call — fast, consistent).
suggestion: K2 Think V2 reasons about the best resolution step.
Set MOCK_AI=1 to skip the K2 API call entirely.
"""
import os
from jinja2 import Environment, FileSystemLoader
from models.k2_think_client import k2_think_complete
import pathlib

_env = Environment(loader=FileSystemLoader(pathlib.Path(__file__).parent / "prompts"))

_MOCK_AI = os.getenv("MOCK_AI", "").lower() in ("1", "true", "yes")

# Hardcoded realistic outputs used when MOCK_AI=1 (no API key needed).
_MOCK_RESPONSES: dict[str, tuple[str, str]] = {
    "host_modified_while_child_owned_by_other": (
        "{acting} is moving the {host_cat} your {child_cat} on {level} is hosted on"
        " — worth a quick chat before either of you syncs.",
        "Ask {acting} to hold off on that {host_cat} move until you relocate"
        " your {child_cat} to the new position.",
    ),
    "element_owned_by_other_session": (
        "You and {owning} are both editing the same {category}"
        " — one of your changes will be lost at sync.",
        "Check with {owning} before syncing; one of you should revert the local change.",
    ),
    "level_deleted_with_owned_elements": (
        "{acting} is deleting {level_name}, which still has {count} elements"
        " owned by {sessions}.",
        "Ask {sessions} to move their elements off {level_name} before completing the deletion.",
    ),
}


def _mock_response(raw: dict) -> dict:
    reason = raw.get("reason_code", "")
    ctx = raw.get("context", {})
    plain_tpl, suggest_tpl = _MOCK_RESPONSES.get(
        reason,
        ("{reason} conflict detected.", "Coordinate with your team before syncing."),
    )

    def _fmt(s: str) -> str:
        return s.format(
            acting=ctx.get("acting_session", "your teammate"),
            owning=ctx.get("owning_session", "your teammate"),
            host_cat=ctx.get("host_category", "element"),
            child_cat=ctx.get("child_category", "dependent element"),
            category=ctx.get("category", "element"),
            level=ctx.get("level", "this level"),
            level_name=ctx.get("level_name", "that level"),
            count=ctx.get("element_count", "several"),
            sessions=", ".join(ctx.get("affected_sessions", ["your teammate"])),
            reason=reason,
        )

    return {"plain_english": _fmt(plain_tpl), "suggestion": _fmt(suggest_tpl)}


def _render(template_name: str, variables: dict) -> str:
    return _env.get_template(template_name).render(**variables)


async def explain_conflict(raw: dict) -> dict:
    if _MOCK_AI:
        return _mock_response(raw)

    context = raw.get("context", {})
    reason = raw.get("reason_code", "")

    # Notification rendered directly from template — fast, consistent, no AI latency.
    plain_english = _render("conflict_explanation.j2", {
        "reason_code": reason,
        "elements": raw.get("elements", []),
        **context,
    }).strip()

    # K2 Think V2 fills in the blank: "Ask [user] to ___"
    acting = context.get("acting_session", "your teammate")
    suggestion_prompt = _render("resolution_suggestion.j2", {
        "plain_english": plain_english,
        "reason_code": reason,
        **context,
    })
    completion = await k2_think_complete(suggestion_prompt)
    # If K2 returned only the completion (not the full sentence), prepend the prefix.
    if completion.lower().startswith("ask "):
        suggestion = completion
    else:
        suggestion = f"Ask {acting} to {completion.rstrip('.')}."

    return {"plain_english": plain_english, "suggestion": suggestion}
