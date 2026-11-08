.PHONY: profile-cached-nodes report-cached-nodes
profile-cached-nodes:
	$(UV) run --locked python scripts/profile_cached_nodes.py

report-cached-nodes:
	$(UV) run --locked python scripts/profile_cached_nodes.py \
		--report results/cached-node-profile/profile.json

.PHONY: profile-policy-rows report-policy-rows
profile-policy-rows:
	$(UV) run --locked python scripts/profile_policy_rows.py

report-policy-rows:
	$(UV) run --locked python scripts/profile_policy_rows.py \
		--report results/row-policy-profile/profile.json

.PHONY: profile-controlled-training report-controlled-training
profile-controlled-training:
	$(UV) run --locked python scripts/profile_controlled_training.py

report-controlled-training:
	$(UV) run --locked python scripts/profile_controlled_training.py \
		--report results/controlled-training-profile/profile.json

.PHONY: check-training-isolation report-training-isolation
# Correctness fixtures and old work audit only; no new postflop learning.
check-training-isolation:
	$(UV) run --locked python scripts/check_training_isolation.py

report-training-isolation:
	$(UV) run --locked python scripts/check_training_isolation.py \
		--replay results/training-isolation/correctness.json

.PHONY: study-policy-swaps report-policy-swaps
study-policy-swaps:
	$(UV) run --locked python scripts/study_policy_swaps.py \
		--output results/runs/policy-swaps/study.json
	$(UV) run --locked --extra solver-validation python scripts/audit_policy_swaps.py \
		--report results/runs/policy-swaps/study.json \
		--output results/runs/policy-swaps/independent.json
	$(UV) run --locked --extra research python scripts/report_policy_swaps.py \
		--report results/runs/policy-swaps/study.json \
		--audit results/runs/policy-swaps/independent.json \
		--output results/runs/policy-swaps/report

report-policy-swaps:
	$(UV) run --locked --extra research python scripts/report_policy_swaps.py

.PHONY: diagnose-range-replies report-range-replies
diagnose-range-replies:
	$(UV) run --locked python scripts/diagnose_range_replies.py \
		--output results/runs/range-mass-replies/diagnosis.json
	$(UV) run --locked --extra solver-validation python scripts/audit_range_replies.py \
		--report results/runs/range-mass-replies/diagnosis.json \
		--output results/runs/range-mass-replies/independent.json
	$(UV) run --locked --extra research python scripts/report_range_replies.py \
		--report results/runs/range-mass-replies/diagnosis.json \
		--audit results/runs/range-mass-replies/independent.json \
		--output results/runs/range-mass-replies/report

report-range-replies:
	$(UV) run --locked --extra research python scripts/report_range_replies.py

.PHONY: study-range-mass report-range-sampled
# Reviewed sampled protocol; ignored outputs and no automatic fresh/global stage.
study-range-mass:
	$(UV) run --locked python scripts/study_range_mass.py \
		--output results/runs/range-mass-sampled/study.json
	$(UV) run --locked --extra solver-validation python scripts/audit_range_sampled.py \
		--report results/runs/range-mass-sampled/study.json \
		--output results/runs/range-mass-sampled/independent.json
	$(UV) run --locked --extra research python scripts/report_range_sampled.py \
		--report results/runs/range-mass-sampled/study.json \
		--audit results/runs/range-mass-sampled/independent.json \
		--output results/runs/range-mass-sampled/report

report-range-sampled:
	$(UV) run --locked --extra research python scripts/report_range_sampled.py

.PHONY: admit-range-mass report-range-mass
# Fixed protocol; training and native audit never run in routine CI.
admit-range-mass:
	$(UV) run --locked --extra jit python scripts/admit_range_mass.py \
		--output results/runs/range-mass-admission/study.json
	$(UV) run --locked --extra solver-validation python scripts/audit_range_mass.py \
		--report results/runs/range-mass-admission/study.json \
		--output results/runs/range-mass-admission/independent.json
	$(UV) run --locked --extra research python scripts/report_range_mass.py \
		--report results/runs/range-mass-admission/study.json \
		--audit results/runs/range-mass-admission/independent.json \
		--output results/runs/range-mass-admission/report

report-range-mass:
	$(UV) run --locked --extra research python scripts/report_range_mass.py

.PHONY: test-range-mass
test-range-mass:
	$(UV) run --locked pytest -q tests/test_range_mass.py tests/test_range_protocol.py

RIVER_DISTINCTION_OUTPUT ?= results/runs/river-distinctions

.PHONY: diagnose-river-distinctions report-river-distinctions
diagnose-river-distinctions:
	$(UV) run --locked python scripts/diagnose_river_distinctions.py --output "$(RIVER_DISTINCTION_OUTPUT)/diagnosis.json"
	$(UV) run --locked --extra solver-validation python scripts/audit_river_distinctions.py --report "$(RIVER_DISTINCTION_OUTPUT)/diagnosis.json" --output "$(RIVER_DISTINCTION_OUTPUT)/independent.json"
	$(UV) run --locked --extra research python scripts/report_river_distinctions.py --report "$(RIVER_DISTINCTION_OUTPUT)/diagnosis.json" --audit "$(RIVER_DISTINCTION_OUTPUT)/independent.json" --output "$(RIVER_DISTINCTION_OUTPUT)/report"

report-river-distinctions:
	$(UV) run --locked --extra research python scripts/report_river_distinctions.py

SAVED_REPLY_OUTPUT ?= results/runs/saved-replies

.PHONY: diagnose-saved-replies report-saved-replies
diagnose-saved-replies:
	$(UV) run --locked python scripts/diagnose_saved_replies.py --output "$(SAVED_REPLY_OUTPUT)/diagnosis.json"
	$(UV) run --locked --extra solver-validation python scripts/audit_saved_replies.py --report "$(SAVED_REPLY_OUTPUT)/diagnosis.json" --output "$(SAVED_REPLY_OUTPUT)/independent.json"
	$(UV) run --locked --extra research python scripts/report_saved_replies.py --report "$(SAVED_REPLY_OUTPUT)/diagnosis.json" --audit "$(SAVED_REPLY_OUTPUT)/independent.json" --output "$(SAVED_REPLY_OUTPUT)/report"

report-saved-replies:
	$(UV) run --locked --extra research python scripts/report_saved_replies.py

UV ?= uv
RIVER_OUTPUT ?= results/runs/river-integration-reproduction
FRESH_OUTPUT ?= results/runs/fresh-validation-reproduction
PUBLIC_BOARD_OUTPUT ?= results/runs/public-board-reproduction
BOARD_DIAGNOSIS_OUTPUT ?= results/runs/board-diagnosis/diagnosis.json
MADE_ADMISSION_OUTPUT ?= results/runs/made-category-admission

.PHONY: admit-made-category report-made-category
admit-made-category:
	$(UV) run --locked --extra jit python scripts/admit_made_category.py --output "$(MADE_ADMISSION_OUTPUT)/study.json"
	$(UV) run --locked --extra solver-validation python scripts/audit_made_category.py --report "$(MADE_ADMISSION_OUTPUT)/study.json" --output "$(MADE_ADMISSION_OUTPUT)/independent.json"
	$(UV) run --locked --extra research python scripts/report_made_category.py --report "$(MADE_ADMISSION_OUTPUT)/study.json" --audit "$(MADE_ADMISSION_OUTPUT)/independent.json" --output "$(MADE_ADMISSION_OUTPUT)/report"

report-made-category:
	$(UV) run --locked --extra research python scripts/report_made_category.py

.PHONY: diagnose-board-collisions
diagnose-board-collisions:
	$(UV) run --locked python scripts/diagnose_board_collisions.py --output "$(BOARD_DIAGNOSIS_OUTPUT)"

.PHONY: study-public-boards report-public-boards

# Clean published source required. A complete negative gate is retained/reported.
study-public-boards:
	$(UV) run --locked --extra jit python scripts/study_public_boards.py --output "$(PUBLIC_BOARD_OUTPUT)/study.json"
	$(UV) run --locked --extra solver-validation python scripts/audit_public_boards.py --report "$(PUBLIC_BOARD_OUTPUT)/study.json" --output "$(PUBLIC_BOARD_OUTPUT)/independent.json"
	$(UV) run --locked --extra research python scripts/report_public_boards.py --report "$(PUBLIC_BOARD_OUTPUT)/study.json" --audit "$(PUBLIC_BOARD_OUTPUT)/independent.json" --output "$(PUBLIC_BOARD_OUTPUT)/report"

# Only own frozen-policy replay plus previously recorded native checks.
report-public-boards:
	$(UV) run --locked --extra research python scripts/report_public_boards.py

.PHONY: fresh-admission validate-fresh-games report-fresh-games

# Verify known development evidence and the published source/input freeze.
fresh-admission:
	$(UV) run --locked python scripts/prepare_fresh_validation.py --gate-only --receipt "$(FRESH_OUTPUT)/admission.json"

# Per-case training; all cells retained even after a performance miss.
validate-fresh-games:
	$(UV) run --locked --extra jit python scripts/validate_fresh_games.py --output "$(FRESH_OUTPUT)/study.json"
	$(UV) run --locked --extra solver-validation python scripts/audit_fresh_games.py --report "$(FRESH_OUTPUT)/study.json" --output "$(FRESH_OUTPUT)/independent.json"
	$(UV) run --locked --extra research python scripts/report_fresh_games.py --report "$(FRESH_OUTPUT)/study.json" --audit "$(FRESH_OUTPUT)/independent.json" --output "$(FRESH_OUTPUT)/report"

report-fresh-games:
	$(UV) run --locked --extra research python scripts/report_fresh_games.py

.PHONY: study-river-integration audit-river-integration report-river-integration

# Full prospective study in ignored output; refuses to overwrite a previous run.
study-river-integration:
	$(UV) run --locked --extra jit python scripts/study_river_integration.py --output "$(RIVER_OUTPUT)/study.json"
	$(UV) run --locked --extra solver-validation python scripts/audit_river_study.py --report "$(RIVER_OUTPUT)/study.json" --output "$(RIVER_OUTPUT)/independent.json"
	$(UV) run --locked --extra research python scripts/report_river_study.py --report "$(RIVER_OUTPUT)/study.json" --audit "$(RIVER_OUTPUT)/independent.json" --output "$(RIVER_OUTPUT)/report"

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

.PHONY: profile-parallel-cells report-parallel-cells
profile-parallel-cells:
	$(UV) run --locked python scripts/profile_parallel_cells.py

report-parallel-cells:
	$(UV) run --locked python scripts/profile_parallel_cells.py \
		--report results/parallel-cell-profile/profile.json

.PHONY: profile-controlled-pipeline audit-controlled-pipeline report-controlled-pipeline
profile-controlled-pipeline:
	$(UV) run --locked --extra research python scripts/profile_controlled_pipeline.py

audit-controlled-pipeline:
	$(UV) run --locked --extra solver-validation python scripts/audit_controlled_pipeline.py

report-controlled-pipeline:
	$(UV) run --locked python scripts/report_controlled_pipeline.py
