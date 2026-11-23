"""Selection-source checks without drawing the registered cohort."""

import sys
from pathlib import Path

import pytest
from numpy.random import PCG64, Generator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from river_generalization.selection import texture_matches  # noqa: E402


def test_published_contract_binds_closed_known_inventory() -> None:
    from turn_exact_transfer_selection import validate_contract

    contract, known = validate_contract(ROOT)
    assert contract["selection_seed"] == 20261520
    assert len(known) == 21
    assert contract["known_mechanistic_spot"] in {
        path.relative_to(ROOT).as_posix() for path in known
    }
    assert contract["paths"] == 8
    assert contract["saved_policy_cases"] == 48


def test_structural_draw_is_deterministic_and_excludes_prior_signature() -> None:
    from turn_exact_transfer_selection import draw_board

    first_rng = Generator(PCG64(7))  # Fictional test stream, not protocol seed.
    first_forbidden: set[tuple[tuple[int, ...], int]] = set()
    board, attempts, signature = draw_board(first_rng, "dry", first_forbidden, 10000)
    assert attempts > 0
    assert texture_matches(board, "dry")
    assert signature in first_forbidden

    repeat_rng = Generator(PCG64(7))
    repeated = draw_board(repeat_rng, "dry", set(), 10000)
    assert repeated == (board, attempts, signature)
    changed_board, changed_attempts, changed_signature = draw_board(
        Generator(PCG64(7)), "dry", {signature}, 10000
    )
    assert texture_matches(changed_board, "dry")
    assert changed_signature != signature
    assert changed_attempts > attempts


def test_structural_attempt_cap_fails_without_replacement() -> None:
    from turn_exact_transfer_selection import draw_board

    with pytest.raises(ArithmeticError, match="attempt cap exceeded"):
        draw_board(Generator(PCG64(7)), "wet", set(), 0)
