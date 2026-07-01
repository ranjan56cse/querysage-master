.PHONY: install lint playground serve

install:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format . --check
	uv run ty check .

playground:
	uv run agents-cli playground

serve:
	uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 9001 --reload
