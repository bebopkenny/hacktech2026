VENV := .venv/bin

# ── Local dev ──────────────────────────────────────────────────────────────────

install:
	python3 -m venv .venv
	$(VENV)/pip install -q -r coordination-service/requirements.txt \
	                       -r ai-layer/requirements.txt

serve-coord:
	cd coordination-service && ../$(VENV)/uvicorn main:app --reload --port 8000

serve-ai:
	cd ai-layer && ../$(VENV)/uvicorn main:app --reload --port 8001

# Run both services (requires two terminals, or use docker-compose instead)
serve: serve-coord serve-ai

# ── Testing ────────────────────────────────────────────────────────────────────

test-coord:
	cd coordination-service && ../../$(VENV)/pytest tests/ -v 2>/dev/null || \
	cd coordination-service && python3 -m pytest tests/ -v

test-ai:
	cd ai-layer && ../$(VENV)/python test_explainer.py

test-harness:
	$(VENV)/python revit-plugin/test_harness.py

test: test-coord test-ai

# ── Docker (prod-like) ─────────────────────────────────────────────────────────

up:
	docker-compose up --build

down:
	docker-compose down

logs:
	docker-compose logs -f

# ── Inject a test event via HTTP (no WS client needed) ────────────────────────

inject-sample:
	curl -s -X POST http://localhost:8000/inject \
	  -H "Content-Type: application/json" \
	  -d @coordination-service/sample_data/sample_events.json | python3 -m json.tool

.PHONY: install serve-coord serve-ai serve test-coord test-ai test-harness test up down logs inject-sample
