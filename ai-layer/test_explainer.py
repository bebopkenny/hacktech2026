"""
Person 4's prompt tuning script. Runs the full explain_conflict() pipeline
against local sample JSON files — no coordination service needed.

Usage:
    # from the ai-layer/ directory
    python test_explainer.py                          # runs all samples
    python test_explainer.py sample_conflicts/host_modified.json
"""
import asyncio
import json
import pathlib
import sys

# Load .env so K2_API_KEY is available without the full Docker stack.
try:
    from dotenv import load_dotenv
    load_dotenv(pathlib.Path(__file__).parent.parent / ".env")
except ImportError:
    pass  # python-dotenv optional; export K2_API_KEY manually if not installed

from explainer import explain_conflict

SAMPLE_DIR = pathlib.Path(__file__).parent / "sample_conflicts"


async def run_one(path: pathlib.Path):
    conflict = json.loads(path.read_text())
    print(f"\n{'='*60}")
    print(f"FILE     : {path.name}")
    print(f"REASON   : {conflict['reason_code']}")
    print(f"ELEMENTS : {conflict['elements']}")
    print(f"MODEL    : {'K2-Think-v2' if len(conflict['elements']) > 1 else 'Gemma'}")
    print("-" * 60)

    result = await explain_conflict(conflict)

    print(f"PLAIN EN : {result['plain_english']}")
    print(f"SUGGEST  : {result['suggestion']}")


async def main():
    targets = [pathlib.Path(p) for p in sys.argv[1:]] if sys.argv[1:] else sorted(SAMPLE_DIR.glob("*.json"))
    if not targets:
        print("No sample conflict files found.")
        return
    for path in targets:
        await run_one(path)
    print(f"\n{'='*60}")
    print(f"Tested {len(targets)} conflict(s).")


asyncio.run(main())
