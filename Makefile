UV ?= uv

.PHONY: study-river-integration audit-river-integration report-river-integration

# Full prospective study; refuses to overwrite an existing report.
study-river-integration:
	$(UV) run --locked --extra jit python scripts/study_river_integration.py
	$(MAKE) audit-river-integration
	$(MAKE) report-river-integration

# Post-training value/BR only; independent outputs never enter own training.
audit-river-integration:
	$(UV) run --locked --extra solver-validation python scripts/audit_river_study.py

# Offline replay of reviewed policies/audit; a failed performance gate is retained.
report-river-integration:
	$(UV) run --locked --extra research python scripts/report_river_study.py

.PHONY: test-river-sampling

# Correctness and resume checks only; starts no variance or learning experiment.
test-river-sampling:
	$(UV) run --locked pytest -q tests/test_river_sampling.py tests/test_postflop_sampling.py

.PHONY: validate-holdem-learning report-holdem-learning

# Bounded diagnostic; a missed performance gate returns nonzero and retains data.
validate-holdem-learning:
	$(UV) run --locked --extra jit --extra solver-validation --extra research python scripts/reproduce_postflop_learning.py

# Fast offline replay of reviewed frozen policies; no training or network games.
report-holdem-learning:
	$(UV) run --locked --extra research python scripts/report_postflop_learning.py

.PHONY: setup lint format typecheck test check hooks validate-five validate-best validate-equity validate-engine validate-cfr train-mccfr-pilot build-card-abstraction train-limit train-no-limit verify-agent validate-solver-tier-a validate-solvers pilot-evaluation evaluate-agents report-evaluation train-slumbot preflight-slumbot benchmark-slumbot analyze-extensions

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

train-mccfr-pilot:
	$(UV) run --locked python scripts/train_mccfr_pilot.py \
		--config configs/mccfr-pilot.json \
		--output results/mccfr-pilot.json

build-card-abstraction:
	$(UV) run --locked --extra research python scripts/build_card_abstraction.py \
		--config configs/card-abstraction.json \
		--output results/card-abstraction.json

train-limit:
	$(UV) run --locked python scripts/train_holdem.py \
		--config configs/limit-training.json \
		--output results/limit-training.json

train-no-limit:
	$(UV) run --locked python scripts/train_holdem.py \
		--config configs/no-limit-training.json \
		--output results/no-limit-training.json

verify-agent:
	$(UV) run --locked python scripts/verify_own_agent.py \
		--config configs/agent-interface-validation.json \
		--output results/agent-interface-validation.json

validate-solver-tier-a:
	$(UV) run --locked --extra solver-validation --extra research python scripts/validate_cfr.py \
		--config configs/solver-validation-tier-a.json \
		--output results/solver-validation/tier-a.json

# Gated full milestone: reference strategies remain comparison artifacts only.
validate-solvers:
	$(UV) run --locked --extra solver-validation --extra validation --extra research python scripts/validate_solvers.py

# Fixed-policy duplicate matches; pilot/main chance seeds are distinct.
pilot-evaluation:
	$(UV) run --locked --extra solver-validation --extra research python scripts/evaluate_agents.py \
		--config configs/match-evaluation.json --mode pilot \
		--output results/runs/evaluation-pilot/pilot.json

evaluate-agents:
	$(UV) run --locked --extra solver-validation --extra research python scripts/evaluate_agents.py \
		--config configs/match-evaluation.json --mode main \
		--output results/evaluation/matches.json
	$(MAKE) report-evaluation

report-evaluation:
	$(UV) run --locked python scripts/audit_match_records.py \
		--report results/evaluation/matches.json --output results/evaluation/record-audit.json
	$(UV) run --locked python scripts/render_evaluation_report.py \
		--report results/evaluation/matches.json

# Own-only matched-depth training; this target makes no network game requests.
train-slumbot:
	$(UV) run --locked python scripts/train_holdem.py \
		--config configs/slumbot-own-training.json \
		--output results/slumbot/own-training.json

preflight-slumbot:
	$(UV) run --locked python scripts/benchmark_slumbot.py --config configs/slumbot-pilot.json

# Explicit live public simulation only; no API calls occur in setup/check/CI.
benchmark-slumbot: preflight-slumbot
	$(UV) run --locked python scripts/benchmark_slumbot.py \
		--config configs/slumbot-pilot.json --live

# Offline own-only learning, exact audits, conditional risk and all tables/figures.
analyze-extensions:
	$(UV) run --locked --extra research python scripts/analyze_extensions.py
