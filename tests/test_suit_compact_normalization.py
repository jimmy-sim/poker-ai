"""Production dispatch preserves card behavior, ownership and failure evidence."""

import copy
import json
import sys
from pathlib import Path
from types import ModuleType

# Private execution modules stay in scripts; allow direct single-file pytest.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest
import suit_candidates_support as kernel
from compact_suit.normalization import Normalization, validate

from poker_ai.abstraction import potential

CONFIG = json.loads(
    (
        Path(__file__).resolve().parents[1] / "configs/compact-suit-pipeline.json"
    ).read_text()
)["normalization"]


def test_live_is_not_restoration_and_original_is_restored() -> None:
    state = Normalization(CONFIG, parent=True)
    with state.installed():
        assert potential.canonical_cards((0, 4), (11, 15, 19)) == kernel.BASE(
            (0, 4), (11, 15, 19)
        )
        assert state.summary()["active"] is True
        with pytest.raises(ArithmeticError):
            validate(state.summary(), CONFIG, parent=True)
    validate(state.summary(), CONFIG, parent=True)
    assert state.reduced_evaluations == 1
    assert potential.canonical_cards is kernel.BASE


def test_worker_does_not_install_or_evaluate_optimized_code() -> None:
    state = Normalization(CONFIG, parent=False)
    with state.installed():
        assert potential.canonical_cards is kernel.BASE
        potential.canonical_cards((0, 4), (11, 15, 19))
    validate(state.summary(), CONFIG, parent=False)
    assert state.requests == 0
    with pytest.raises(ArithmeticError):
        validate(state.summary(), CONFIG, parent=True)


def test_primary_exception_and_late_alias_restoration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    late = ModuleType("poker_ai.test_late_suit_alias")
    import sys

    monkeypatch.setitem(sys.modules, late.__name__, late)
    state = Normalization(CONFIG, parent=True)
    with pytest.raises(LookupError, match="primary"):
        with state.installed():
            vars(late)["call"] = potential.canonical_cards
            raise LookupError("primary")
    assert vars(late)["call"] is kernel.BASE
    assert potential.canonical_cards is kernel.BASE
    assert state.restored is True and state.status == "failed_retained"
    with pytest.raises(ArithmeticError):
        validate(state.summary(), CONFIG, parent=True)


def test_scope_cannot_be_reused_or_nested() -> None:
    state = Normalization(CONFIG, parent=True)
    with state.installed():
        with pytest.raises(ArithmeticError):
            with Normalization(CONFIG, parent=True).installed():
                pytest.fail("nested normalization")
    with pytest.raises(ArithmeticError):
        with state.installed():
            pytest.fail("reused normalization")


def test_unsupported_and_changed_dependencies_use_original(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = Normalization(CONFIG, parent=True)
    with state.installed():
        assert vars(potential)["canonical_cards"]([0, 1], [2, 3, 4]) == vars(kernel)[
            "BASE"
        ]([0, 1], [2, 3, 4])
        with monkeypatch.context() as patch:
            patch.setattr(kernel, "dependencies_unchanged", lambda: False)
            assert potential.canonical_cards((0, 1), ()) == kernel.BASE((0, 1), ())
    validate(state.summary(), CONFIG, parent=True)
    assert state.fallbacks == state.original_evaluations == 2
    assert state.reduced_evaluations == 0


def test_request_cap_and_original_error_are_recorded() -> None:
    config = dict(CONFIG, maximum_parent_requests=1)
    state = Normalization(config, parent=True)
    with state.installed():
        with pytest.raises(ValueError, match="duplicate card"):
            potential.canonical_cards((0, 0), ())
        with pytest.raises(ArithmeticError, match="cap"):
            potential.canonical_cards((0, 4), ())
    assert state.requests == 1 and state.errors == 2
    with pytest.raises(ArithmeticError):
        validate(state.summary(), config, parent=True)


@pytest.mark.parametrize(
    "field,value",
    [
        ("enabled", 1),
        ("active", 0),
        ("restored", 1),
        ("requests", False),
        ("pid", True),
        ("thread", 0),
        ("aliases_remaining", False),
        ("status", "running"),
        ("scope", "another implementation"),
        ("geometry_sha256", "0" * 64),
        ("table_sha256", "0" * 64),
        ("role", "worker"),
        ("original_evaluations", 1),
        ("errors", 1),
    ],
)
def test_final_state_rejects_typed_or_context_corruption(
    field: str, value: object
) -> None:
    state = Normalization(CONFIG, parent=True)
    with state.installed():
        potential.canonical_cards((0, 4), ())
    row = copy.deepcopy(state.summary())
    row[field] = value
    with pytest.raises(ArithmeticError):
        validate(row, CONFIG, parent=True)
