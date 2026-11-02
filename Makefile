UV ?= uv

.PHONY: setup lint format typecheck test check hooks

setup:
	$(UV) sync --locked --dev

lint:
	$(UV) run --locked ruff check .
	$(UV) run --locked ruff format --check .

format:
	$(UV) run --locked ruff check --fix .
	$(UV) run --locked ruff format .

typecheck:
	$(UV) run --locked mypy --strict src tests

test:
	$(UV) run --locked pytest -q -m "not slow"

check: lint typecheck test

hooks:
	$(UV) run --locked pre-commit install
