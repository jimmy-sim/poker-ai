"""Hand-computed local disagreements and static observable feature controls."""

import copy
import importlib.util
import itertools
import json
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

from poker_ai.abstraction.range_mass import RangePrior, mass_bin
from poker_ai.cards import parse_card
from poker_ai.postflop.game import SpotState, load_spot

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "river_refinement_cli", ROOT / "scripts/diagnose_river_refinement.py"
)
assert SPEC is not None and SPEC.loader is not None
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)


def cards(text: str) -> tuple[int, ...]:
    return tuple(parse_card(c) for c in text.split())


def row(i: int, q: list[float], mass: float, relations: list[int]) -> dict[str, Any]:
    # Fictional equally weighted opponent combinations; not poker outcomes.
    masses = [Fraction(relations.count(k), len(relations)) for k in range(4)]
    return dict(
        exact_info=i,
        parent=7,
        target=0,
        street="RIVER",
        actions=["fold", "call"],
        counterfactual_mass=mass,
        q={s: q[:] for s in CLI.SUFFIXES},
        features=dict(
            bins=[mass_bin(m) for m in masses],
            masses=[[m.numerator, m.denominator] for m in masses],
            relations=relations,
        ),
    )


def table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], CLI.summarize(rows, 0)["probes"])


def test_weighted_cost_hand_computed_and_identity_refinement() -> None:
    rows = [row(0, [3, 0], 1, [1, 3]), row(1, [0, 2], 3, [3, 1])]
    before = copy.deepcopy(rows)
    result = CLI.summarize(rows, 0)
    # Weights 1/4,3/4. Separate maxima total 2.25; shared call earns1.5.
    probes = result["probes"]
    assert [p["groups"] for p in probes] == [1, 1, 2, 2]
    assert result["q8_exact_mass_same_partition"] is True
    for suffix in CLI.SUFFIXES:
        assert [
            p["panels"][suffix]["local_sharing_cost_chips_per_cf_decision"]
            for p in probes
        ] == pytest.approx([0.75, 0.75, 0, 0])
        assert [p["panels"][suffix]["unresolved_parents"] for p in probes] == [
            1,
            1,
            0,
            0,
        ]
    assert rows == before


def test_precision_probe_can_split_equal_bins_with_different_exact_mass() -> None:
    # Synthetic16-combo prior: loss 1/16 versus0 both in bin0; win7/8 vs15/16 bin7.
    a = row(0, [3, 0], 1, [0] + [1] + [3] * 14)
    b = row(1, [0, 2], 1, [0] + [3] * 15)
    result = CLI.summarize([a, b], 0)
    assert result["q8_exact_mass_same_partition"] is False
    assert [p["groups"] for p in result["probes"]] == [1, 2, 2, 2]
    assert (
        result["probes"][1]["panels"]["exact"][
            "local_sharing_cost_chips_per_cf_decision"
        ]
        == 0
    )


def test_common_tie_is_not_a_strict_conflict_and_unsupported_rows_retained() -> None:
    rows = [
        row(0, [1, 1], 1, [1, 3]),
        row(1, [0, 2], 1, [1, 3]),
        row(2, [100, -100], 0, [3, 1]),
    ]
    result = CLI.summarize(rows, 0)
    assert (
        result["river_infos"],
        result["supported_infos"],
        result["unsupported_infos"],
    ) == (3, 2, 1)
    for p in result["probes"]:
        assert p["panels"]["exact"]["unresolved_parents"] == 0
        assert p["panels"]["exact"]["local_sharing_cost_chips_per_cf_decision"] == 0


def test_all_zero_support_is_explicitly_no_evidence() -> None:
    result = CLI.summarize([row(0, [3, 0], 0, [1, 3]), row(1, [0, 2], 0, [1, 3])], 0)
    assert result["no_supported_evidence"] is True
    assert result["supported_infos"] == 0
    assert all(
        p["panels"]["exact"]["local_sharing_cost_chips_per_cf_decision"] == 0
        for p in result["probes"]
    )


@pytest.mark.parametrize(
    "bad",
    [
        "duplicate",
        "owner",
        "owner_bool",
        "parent",
        "menu",
        "illegal",
        "nan",
        "negative_mass",
        "nan_mass",
        "width",
        "street",
        "bins",
        "mass",
        "relations",
    ],
)
def test_malformed_panel_rejected(bad: str) -> None:
    a, b = row(0, [3, 0], 1, [1, 3]), row(1, [0, 2], 1, [1, 3])
    if bad == "duplicate":
        b["exact_info"] = 0
    elif bad == "owner":
        b["target"] = 1
    elif bad == "owner_bool":
        b["target"] = False
    elif bad == "parent":
        b["parent"] = -1
    elif bad == "menu":
        b["actions"] = ["check", "raise"]
    elif bad == "illegal":
        b["actions"] = ["call", "call"]
    elif bad == "nan":
        b["q"]["exact"][0] = float("nan")
    elif bad == "negative_mass":
        b["counterfactual_mass"] = -1
    elif bad == "nan_mass":
        b["counterfactual_mass"] = float("nan")
    elif bad == "width":
        b["q"]["exact"] = [1]
    elif bad == "street":
        b["street"] = "TURN"
    elif bad == "bins":
        b["features"]["bins"] = [0, 0, 0, 7]
    elif bad == "mass":
        b["features"]["masses"][1] = [1, 0]
    else:
        b["features"]["relations"] = [True, 3]
    with pytest.raises(ArithmeticError):
        CLI.summarize([a, b], 0)


def test_q8_parent_cannot_merge_distinct_bins() -> None:
    with pytest.raises(ArithmeticError, match="incompatible mass bins"):
        table([row(0, [3, 0], 1, [1, 3]), row(1, [0, 2], 1, [3, 3])])


def test_one_unresolved_parent_counted_once_and_panels_kept_separate() -> None:
    rows = [
        row(0, [3, 0], 1, [1, 3]),
        row(1, [0, 2], 1, [1, 3]),
        row(2, [4, 0], 1, [3, 1]),
        row(3, [0, 5], 1, [3, 1]),
    ]
    for r in rows:
        r["q"]["restricted"] = [1, 0]
    probes = table(rows)
    assert probes[2]["panels"]["exact"]["unresolved_parents"] == 1
    assert probes[2]["panels"]["restricted"]["unresolved_parents"] == 0
    assert probes[3]["panels"]["exact"]["unresolved_parents"] == 0


def test_two_unit_weight_combos_make_q8_injective_on_all_attainable_masses() -> None:
    by_bins: dict[Any, Any] = {}
    for pair in itertools.product(range(4), repeat=2):
        masses = tuple(Fraction(pair.count(i), 2) for i in range(4))
        bins = tuple(mass_bin(m) for m in masses)
        assert by_bins.setdefault(bins, masses) == masses


def test_actual_static_features_are_canonical_and_expose_blocker() -> None:
    prior = RangePrior.create([(cards("Kh Qh"), 1), (cards("9c 9d"), 1)])
    a = CLI.features(cards("Tc Td"), cards("Ts 9s 4d 2h 9h"), prior)
    b = CLI.features(cards("Tc Td"), cards("Ts 9s 4d 2h 9d"), prior)
    assert a["masses"] == [[0, 1], [1, 2], [0, 1], [1, 2]]
    assert b["masses"] == [[1, 2], [0, 1], [0, 1], [1, 2]]
    assert a["relations"] != b["relations"]
    reverse = RangePrior.create([(cards("9d 9c"), 10), (cards("Qh Kh"), 10)])
    assert CLI.features(cards("Td Tc"), cards("4d 9s Ts 2h 9h"), reverse) == a


def test_hidden_opponent_and_future_worlds_do_not_enter_static_features() -> None:
    spot = load_spot(ROOT / "configs/learning-spots/dev_medium_oop.json")
    prior = RangePrior.create((h.cards, h.weight) for h in spot.ranges[1])
    first = SpotState(spot).child(0).child(0)
    second = SpotState(spot).child(0).child(1)
    worlds = [
        first.child(parse_card("9h")),
        first.child(parse_card("3c")),
        second.child(parse_card("9h")),
    ]
    early = []
    for state in worlds:
        assert state.dealer is not None
        obs = state.dealer.observe(0)
        early.append((obs.hole_cards, obs.board))
        with pytest.raises(ValueError):
            CLI.features(obs.hole_cards, obs.board, prior)
    assert early[0] == early[1] == early[2]  # Future cards not yet observed.
    signatures = []
    for state in (worlds[0], worlds[2]):
        state = state.child(1).child(1)
        assert state.dealer is not None
        obs = state.dealer.observe(0)
        signatures.append(CLI.features(obs.hole_cards, obs.board, prior))
    assert signatures[0] == signatures[1]


def test_deterministic_archive_and_existing_output_retained(tmp_path: Path) -> None:
    payload = dict(rows=[row(0, [3, 0], 1, [1, 3])])
    a, b = tmp_path / "a.gz", tmp_path / "b.gz"
    CLI.write_gzip(a, payload)
    CLI.write_gzip(b, payload)
    assert a.read_bytes() == b.read_bytes()
    folder = tmp_path / "partial"
    folder.mkdir()
    marker = folder / "keep"
    marker.write_text("original")
    with pytest.raises(FileExistsError):
        CLI.run(tmp_path, folder)
    assert marker.read_text() == "original"


def test_source_config_binding() -> None:
    assert CLI.digest(ROOT / CLI.CONFIG) == CLI.CONFIG_SHA
    cfg = json.loads((ROOT / CLI.CONFIG).read_text())
    assert tuple(cfg["suffixes"]) == CLI.SUFFIXES
    assert tuple(cfg["probes"]) == CLI.PROBES
    assert CLI.digest(ROOT / cfg["panel_config"]) == cfg["panel_config_sha256"]


def test_weights_scale_invariance_and_permutation() -> None:
    rows = [row(0, [3, 0], 1, [1, 3]), row(1, [0, 2], 3, [3, 1])]
    expected = table(rows)
    rows.reverse()
    for r in rows:
        r["counterfactual_mass"] *= 13
    assert table(rows) == expected
    assert np.isfinite(
        expected[0]["panels"]["exact"]["local_sharing_cost_chips_per_cf_decision"]
    )


@pytest.mark.parametrize("failure", ["exception", "timeout", "changed_input"])
def test_incomplete_execution_retains_progress_and_never_reports_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    cfg = json.loads((ROOT / CLI.CONFIG).read_text())
    for name in (CLI.CONFIG, cfg["panel_config"]):
        dest = tmp_path / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT / name).read_bytes())
    for name in (cfg["own"], cfg["native"]):
        dest = tmp_path / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("fictional input; no poker runner used")
    monkeypatch.setattr(
        CLI, "source_provenance", lambda *a, **k: dict(dirty=False, sha256={})
    )

    def stop(root: Path, output: Path, *a: Any) -> None:
        (output / "retained.json").write_text('{"fixture":true}')
        if failure == "exception":
            raise RuntimeError("fixture interrupted")
        if failure == "timeout":
            raise TimeoutError("fixture cap")
        (root / cfg["own"]).write_text("fixture input changed")

    monkeypatch.setattr(CLI, "calculate", stop)
    output = tmp_path / "out"
    with pytest.raises((RuntimeError, TimeoutError, ArithmeticError)):
        CLI.run(tmp_path, output)
    assert (output / "retained.json").read_text() == '{"fixture":true}'
    assert (output / "partial.json").is_file()
    assert json.loads((output / "failure.json").read_text())["type"] in {
        "RuntimeError",
        "TimeoutError",
        "ArithmeticError",
    }
    assert not (output / "manifest.json").exists()


def test_timeout_after_manifest_is_retained_as_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = json.loads((ROOT / CLI.CONFIG).read_text())
    for name in (CLI.CONFIG, cfg["panel_config"]):
        dest = tmp_path / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT / name).read_bytes())
    for name in (cfg["own"], cfg["native"]):
        dest = tmp_path / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("fictional input")
    monkeypatch.setattr(
        CLI, "source_provenance", lambda *a, **k: dict(dirty=False, sha256={})
    )
    monkeypatch.setattr(CLI, "calculate", lambda *a: None)

    class Deadline:
        def __init__(self, seconds: float) -> None:
            self.started = 0.0
            self.calls = 0

        def check(self) -> None:
            self.calls += 1
            if self.calls == 2:
                raise TimeoutError("fixture serialization cap")

    monkeypatch.setattr(CLI, "Deadline", Deadline)
    output = tmp_path / "out"
    with pytest.raises(TimeoutError):
        CLI.run(tmp_path, output)
    assert (
        json.loads((output / "manifest.json").read_text())["status"]
        == "failed_saved_river_refinement_diagnostic"
    )
    assert (output / "failure.json").is_file()
