.PHONY: install lint playground run serve test generate-traces grade

install:
	uv sync

lint:
	uv run agents-cli lint

playground:
	uv run agents-cli playground

run:
	uv run agents-cli run --query "$(query)"

serve:
	uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 --reload

test:
	uv run pytest tests/

generate-traces:
	uv run agents-cli eval generate

grade:
	uv run agents-cli eval grade
