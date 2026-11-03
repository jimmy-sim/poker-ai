UV ?= uv

.PHONY: setup lint format typecheck test check hooks validate-five validate-best validate-equity validate-engine validate-cfr

setup:
	$(UV) sync --locked --dev

lint:
	$(UV) run --locked ruff check .
	$(UV) run --locked ruff format --check .

format:
	$(UV) run --locked ruff check --fix .
	$(UV) run --locked ruff format .

typecheck:
	$(UV) run --locked mypy --strict src tests scripts

test:
	$(UV) run --locked pytest -q -m "not slow"

check: lint typecheck test

hooks:
	$(UV) run --locked pre-commit install

# Exhaustive independent reference check; kept outside routine CI.
validate-five:
	$(UV) run --locked --extra validation python scripts/validate_five.py \
		--config configs/five-card-exhaustive.json \
		--output results/five-card-exhaustive.json

# Fixed-seed million-hand checks for both six and seven cards.
validate-best:
	$(UV) run --locked --extra validation python scripts/validate_best.py \
		--config configs/best-five-validation.json \
		--output results/best-five-direct-validation.json

validate-equity:
	$(UV) run --locked --extra validation python scripts/validate_equity.py \
		--config configs/equity-validation.json \
		--output results/equity-validation.json

validate-engine:
	$(UV) run --locked --extra engine-validation python scripts/validate_engine.py \
		--config configs/engine-validation.json \
		--output results/engine-validation.json

# Original Phase 2 toy-game acceptance, separate from gated Phase 3.5.
validate-cfr:
	$(UV) run --locked --extra solver-validation --extra research python scripts/validate_cfr.py \
		--config configs/cfr-validation.json \
		--output results/cfr-validation.json
