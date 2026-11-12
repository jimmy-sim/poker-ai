"""Scalar/protocol/cache tests; all generated parents are fictional UNIT data."""

import copy
import gzip
import itertools
import json
import pkgutil
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from poker_ai.cards import parse_card
from poker_ai.evaluation import range_blocker_io as io
from poker_ai.evaluation import range_blocker_probe as probe
from poker_ai.evaluation import range_blocker_run as runner
from poker_ai.evaluation import range_blocker_view as view
from poker_ai.evaluation.opponent_decision_run import BLOCKED
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]
RANGES = (
    ((parse_card("Js"), parse_card("As")), (parse_card("Tc"), parse_card("Td"))),
    ((parse_card("Qh"), parse_card("Kh")), (parse_card("9c"), parse_card("9d"))),
)


def source_case(arm: str = "coarse_self") -> tuple[dict[str, Any], dict[str, Any]]:
    """Manually known half-weight conflict; NOT a measured poker policy."""
    responses, details = [], []
    for target in (0, 1):
        hole = ["Js", "As"] if target == 0 else ["Qh", "Kh"]
        opposite = (
            [["Qh", "Kh"], ["9c", "9d"]]
            if target == 0
            else [["Js", "As"], ["Tc", "Td"]]
        )
        rows: list[dict[str, Any]] = []
        for index, river in enumerate(("9d", "9h", "5d")):
            board = ["Ts", "9s", "4d", "2h", river]
            known = set(board + hole)
            q = [[-1.0, 1.0], [-1.0, -3.0], [0.0, 0.0]][index]
            rows.append(
                dict(
                    exact_info=target * 3 + index,
                    hole=hole,
                    board=board,
                    pot=2,
                    actions=["fold", "raise_to 2"],
                    compatible=[set(h).isdisjoint(known) for h in opposite],
                    counterfactual_support=1.0 if index < 2 else 0.0,
                    uniform_decision_weight=[0.25, 0.25, 0.5][index],
                    actual_action_values_chips=q,
                    prior_action_values_chips=q.copy(),
                )
            )
        coarse = target == 1 and arm != "fine_self"
        member_lists = [[3, 4], [5]] if coarse else [[r["exact_info"]] for r in rows]
        groups = []
        for index, infos in enumerate(member_lists):
            active = [i for i in infos if i % 3 < 2]
            groups.append(
                dict(
                    group_id=f"UNIT_ONLY/{target}/{index}",
                    infos=infos,
                    supported_infos=active,
                    supported_rows=len(active),
                    weight=0.25 * len(active),
                    local_cost=0.5 if len(active) == 2 else 0.0,
                    strict_conflict=len(active) == 2,
                )
            )
        metrics = dict(
            local_sharing_cost_chips_per_weighted_decision=0.5 if coarse else 0.0,
            strict_conflicting_groups=1 if coarse else 0,
            total_groups=len(groups),
            supported_groups=len(groups) - 1,
            supported_uniform_decision_weight=0.5,
        )
        suffixes, full = [], []
        for label in probe.SUFFIXES:
            suffixes.append(
                dict(
                    suffix=label,
                    river_info_ids=[r["exact_info"] for r in rows],
                    panels=[
                        dict(
                            range_weights=w,
                            group_controls={
                                "full_static_probe_refinement": copy.deepcopy(metrics)
                            },
                        )
                        for w in probe.WEIGHTS
                    ],
                )
            )
            full.append(
                dict(
                    suffix=label,
                    rows=copy.deepcopy(rows),
                    groups={
                        w: {"full_static_probe_refinement": copy.deepcopy(groups)}
                        for w in probe.WEIGHTS
                    },
                )
            )
        responses.append(dict(target=target, suffixes=suffixes))
        details.append(
            dict(target=target, declared_opponent_range=opposite, suffixes=full)
        )
    return dict(game="UNIT_GAME", arm=arm, responses=responses), dict(responses=details)


def test_scalar_and_refinement_controls_keep_original_half_weight() -> None:
    profile, detail = source_case()
    before = json.dumps((profile, detail), sort_keys=True)
    summary, full = probe.analyse(profile, detail, probe.FeatureBook())
    assert json.dumps((profile, detail), sort_keys=True) == before
    for suffix in summary["responses"][1]["suffixes"]:
        for w in suffix["panels"]:
            metrics = w["group_controls"]
            assert (
                metrics["source_static"][
                    "local_sharing_cost_chips_per_weighted_decision"
                ]
                == 0.5
            )
            assert metrics["source_static"]["source_conflicting_groups_resolved"] == 0
            for name in probe.CONTROLS[1:]:
                assert (
                    metrics[name]["local_sharing_cost_chips_per_weighted_decision"] == 0
                )
                assert metrics[name]["source_conflicting_groups_resolved"] == 1
            assert all(
                m["supported_uniform_decision_weight"] == 0.5 for m in metrics.values()
            )
    assert len(full["responses"][1]["row_features"]) == 3
    assert len(full["responses"][1]["partitions"][-1]["groups"]) == 3


def test_same_masks_on_different_boards_do_not_secretly_use_board_identity() -> None:
    _, detail = source_case()
    source = detail["responses"][1]["suffixes"][0]
    source["rows"][0]["board"][-1] = "5c"
    source["rows"][1]["board"][-1] = "5h"
    book = probe.FeatureBook()
    _, partitions = probe.geometry("UNIT", 1, RANGES, source, book)
    assert len(book.features) == 3
    for partition in partitions[:-1]:
        assert partition["groups"][0]["infos"] == [3, 4]
    assert len(partitions[-1]["groups"]) == 3


def test_both_public_can_split_when_own_mask_and_actual_opponent_mask_do_not() -> None:
    # UNIT numerical control, not a measured policy. One opponent alternative
    # overlaps our actual As, yet remains relevant to the full public catalog.
    _, detail = source_case()
    source = detail["responses"][1]["suffixes"][0]
    ranges = (
        ((parse_card("As"), parse_card("Kd")), (parse_card("5d"), parse_card("6d"))),
        ((parse_card("As"), parse_card("Qh")), (parse_card("Tc"), parse_card("Td"))),
    )
    for row, river in zip(source["rows"], ("Qh", "Qc", "5d"), strict=True):
        row["hole"] = ["As", "Kd"]
        row["board"][-1] = river
        row["compatible"] = [False, True]
    _, partitions = probe.geometry("UNIT", 0, ranges, source, probe.FeatureBook())
    old = source["groups"][probe.WEIGHTS[0]]["full_static_probe_refinement"]
    metrics = dict(
        total_groups=2,
        supported_groups=1,
        strict_conflicting_groups=1,
        local_sharing_cost_chips_per_weighted_decision=0.5,
        supported_uniform_decision_weight=0.5,
    )
    scores, _, _, _ = probe.score(
        source["rows"], partitions, probe.FIELDS[0], old, metrics
    )
    assert scores["own_public"]["local_sharing_cost_chips_per_weighted_decision"] == 0.5
    assert scores["both_public"]["local_sharing_cost_chips_per_weighted_decision"] == 0
    assert scores["both_public"] == scores["both_public_joint"]


def test_private_projection_wrong_menu_and_range_order_guards() -> None:
    _, detail = source_case()
    source = detail["responses"][1]["suffixes"][0]
    bad = copy.deepcopy(source)
    bad["rows"][0]["compatible"][0] = False
    with pytest.raises(ArithmeticError, match="projection"):
        probe.geometry("UNIT", 1, RANGES, bad, probe.FeatureBook())
    bad = copy.deepcopy(source)
    bad["rows"][1]["actions"] = ["check", "raise_to 2"]
    with pytest.raises(ArithmeticError, match="menu"):
        probe.geometry("UNIT", 1, RANGES, bad, probe.FeatureBook())
    book = probe.FeatureBook()
    book.bind("UNIT", RANGES, source["rows"][0]["board"])
    with pytest.raises(ArithmeticError, match="ranges changed"):
        book.bind("UNIT", tuple(reversed(RANGES)), source["rows"][0]["board"])
    book.frozen = True
    with pytest.raises(ArithmeticError, match="lacks"):
        book.bind("UNIT", RANGES, ["Ts", "9s", "4d", "2h", "8c"])


@pytest.mark.parametrize(
    "change", ["support", "weight", "membership", "source_cost", "source_conflict"]
)
def test_bound_source_invariants_are_not_silently_changed(change: str) -> None:
    profile, detail = source_case()
    second = detail["responses"][1]["suffixes"][1]
    if change == "support":
        second["rows"][0]["counterfactual_support"] = 0.0
    elif change == "weight":
        second["rows"][0]["uniform_decision_weight"] = 0.75
    elif change == "membership":
        second["groups"][probe.WEIGHTS[0]]["full_static_probe_refinement"][0][
            "infos"
        ].pop()
    elif change == "source_cost":
        second["groups"][probe.WEIGHTS[0]]["full_static_probe_refinement"][0][
            "local_cost"
        ] += 0.01
    else:
        second["groups"][probe.WEIGHTS[0]]["full_static_probe_refinement"][0][
            "strict_conflict"
        ] = False
    with pytest.raises(ArithmeticError):
        probe.analyse(profile, detail, probe.FeatureBook())


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True])
def test_nonfinite_and_boolean_numeric_values_rejected_even_off_support(
    value: float,
) -> None:
    _, detail = source_case()
    rows = detail["responses"][1]["suffixes"][0]["rows"]
    rows[-1]["actual_action_values_chips"][0] = value
    with pytest.raises(ArithmeticError):
        probe.local(rows, probe.FIELDS[0])


def test_singleton_fine_source_and_tied_actions() -> None:
    p, d = source_case("fine_self")
    s, _ = probe.analyse(p, d, probe.FeatureBook())
    assert all(
        m["local_sharing_cost_chips_per_weighted_decision"] == 0
        for r in s["responses"]
        for suffix in r["suffixes"]
        for w in suffix["panels"]
        for m in w["group_controls"].values()
    )
    rows = d["responses"][1]["suffixes"][0]["rows"][:2]
    for r in rows:
        r[probe.FIELDS[0]] = [3.0, 3.0]
    assert probe.local(rows, probe.FIELDS[0]) == dict(
        cost=0.0, conflict=False, weight=0.5
    )


def fake_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Every publication/source gate is mocked ONLY for explicit UNIT parents."""
    config = copy.deepcopy(io.contract(ROOT))
    config["expected_profile_river_rows"] = 144
    config["expected_suffix_river_rows"] = 288
    profiles = []
    details = {}
    for coordinate, (game, seed) in enumerate(
        itertools.product(config["games"], config["seeds"])
    ):
        for arm in config["arms"]:
            p, d = source_case(arm)
            p.update(
                coordinate=coordinate,
                game=game,
                seed=seed,
                source_id=f"UNIT_ONLY/{coordinate}/{arm}",
                policy_sha256="a" * 64,
                details_file=f"UNIT_ONLY/{coordinate}-{arm}.json.gz",
                _detail_sha256="b" * 64,
            )
            profiles.append(p)
            details[p["source_id"]] = d
    for module in (io, runner):
        monkeypatch.setattr(module, "contract", lambda root: config)
        monkeypatch.setattr(module, "parents", lambda *args: profiles)
        monkeypatch.setattr(
            module, "source_detail", lambda root, p: details[p["source_id"]]
        )
    required = {
        io.CONFIG,
        *io.ENTRIES,
        *(
            f"src/poker_ai/evaluation/range_blocker_{n}.py"
            for n in ("features", "probe", "io", "run", "view")
        ),
    }
    provenance = dict(
        dirty=False,
        git_commit="UNIT_ONLY_NOT_A_SCIENTIFIC_RECEIPT",
        sha256={k: "0" * 64 for k in required | {"UNIT_ONLY"}},
    )
    monkeypatch.setattr(runner, "source_provenance", lambda *args, **kwargs: provenance)
    monkeypatch.setattr(io, "check_source", lambda *args: None)
    return config, profiles, details


def make_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fake_inputs(monkeypatch)
    folder = tmp_path / "cache"
    runner.run(tmp_path, folder, time.perf_counter())
    return folder


def test_complete_unit_command_cache_csv_and_lazy_inspector(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = make_cache(tmp_path, monkeypatch)
    cache = io.load(tmp_path, folder)
    assert len(cache.profiles) == 24
    assert len(io.csv_rows(cache.profiles)) == 960
    for p in cache.profiles:
        d, _ = cache.detail(p)
        assert len(d["responses"]) == 2
    view.show(cache, cache.profiles[0], 1, 0, 1)
    assert "public cards only" in capsys.readouterr().out
    monkeypatch.setattr(view, "load", lambda *args: cache)
    keys = iter(["n", "p", "s", "o", "g", "t", "r", "?", "q"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(keys))
    monkeypatch.setattr(sys, "argv", ["inspect", "--interactive"])
    assert view.main(tmp_path) == 0
    assert "Choose n, p" in capsys.readouterr().out
    with pytest.raises(ValueError, match="positive"):
        view.show(cache, cache.profiles[0], 1, 0, 0)


def test_interruption_retains_complete_profile_and_public_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_inputs(monkeypatch)
    real = probe.analyse
    calls = 0

    def interrupted(*args: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KeyboardInterrupt("UNIT interruption")
        return real(*args)

    monkeypatch.setattr(runner, "analyse", interrupted)
    folder = tmp_path / "partial"
    with pytest.raises(KeyboardInterrupt):
        runner.run(tmp_path, folder, time.perf_counter())
    assert json.loads((folder / "failure.json").read_text())["completed_profiles"] == 1
    assert len(json.loads((folder / "partial.json").read_text())["profiles"]) == 1
    assert json.loads((folder / "catalog.json").read_text())["features"]
    assert len(list((folder / "details").glob("*.gz"))) == 1
    with pytest.raises(ArithmeticError, match="interrupted"):
        io.load(tmp_path, folder)
    with pytest.raises(FileExistsError):
        runner.run(tmp_path, folder, time.perf_counter())


def test_constructor_and_deadline_failures_retained_before_new_profiles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_inputs(monkeypatch)

    def forbidden_parent(*args: Any) -> list[dict[str, Any]]:
        for name in BLOCKED:
            with pytest.raises(AssertionError, match="learner/reference"):
                pkgutil.resolve_name(name)()
        raise RuntimeError("UNIT blocked checks complete")

    monkeypatch.setattr(runner, "parents", forbidden_parent)
    with pytest.raises(RuntimeError):
        runner.run(tmp_path, tmp_path / "blocked", time.perf_counter())
    assert (
        json.loads((tmp_path / "blocked/failure.json").read_text())[
            "completed_profiles"
        ]
        == 0
    )
    fake_inputs(monkeypatch)
    with pytest.raises(TimeoutError):
        runner.run(tmp_path, tmp_path / "expired", time.perf_counter() - 901)
    assert (
        json.loads((tmp_path / "expired/failure.json").read_text())[
            "completed_profiles"
        ]
        == 0
    )


def rehash(folder: Path, name: str) -> None:
    path = folder / "manifest.json"
    m = json.loads(path.read_text())
    m["outputs"][name] = digest(folder / name)
    path.write_text(json.dumps(m))


@pytest.mark.parametrize(
    "change",
    [
        "missing_profile",
        "missing_panel",
        "bad_cost",
        "bad_weight",
        "bool_count",
        "singleton",
        "nan",
        "source_identity",
    ],
)
def test_summary_schema_rejects_incomplete_or_false_results(
    change: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = make_cache(tmp_path, monkeypatch)
    p = folder / "summary.json"
    data = json.loads(p.read_text())
    profiles = data["profiles"]
    w = profiles[0]["responses"][1]["suffixes"][0]["panels"][0]
    if change == "missing_profile":
        profiles.pop()
    elif change == "missing_panel":
        w["group_controls"].pop("own_public")
    elif change == "bad_cost":
        w["group_controls"]["own_public"][
            "local_sharing_cost_chips_per_weighted_decision"
        ] = 2.0
    elif change == "bad_weight":
        w["group_controls"]["own_public"]["supported_uniform_decision_weight"] = True
    elif change == "bool_count":
        w["group_controls"]["own_public"]["total_groups"] = True
    elif change == "singleton":
        w["group_controls"]["exact_information"][
            "local_sharing_cost_chips_per_weighted_decision"
        ] = 0.1
    elif change == "nan":
        w["maximum_source_chip_error"] = float("nan")
    else:
        profiles[0]["policy_sha256"] = "c" * 64
    p.write_text(json.dumps(data))
    rehash(folder, "summary.json")
    with pytest.raises((ArithmeticError, ValueError)):
        io.load(tmp_path, folder)


@pytest.mark.parametrize(
    "change", ["group", "cost", "binding", "catalog", "lazy_bytes", "csv", "failed"]
)
def test_detail_catalog_and_publication_corruption_rejected(
    change: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = make_cache(tmp_path, monkeypatch)
    if change == "catalog":
        p = folder / "catalog.json"
        data = json.loads(p.read_text())
        next(iter(data["features"].values()))["available"][0][0] = False
        p.write_text(json.dumps(data))
        rehash(folder, "catalog.json")
        with pytest.raises(ArithmeticError):
            io.load(tmp_path, folder)
        return
    if change == "csv":
        (folder / "panels.csv").write_text("UNIT corrupt CSV")
        rehash(folder, "panels.csv")
        with pytest.raises(ArithmeticError):
            io.load(tmp_path, folder)
        return
    if change == "failed":
        (folder / "failure.json").write_text("{}")
        with pytest.raises(ArithmeticError):
            io.load(tmp_path, folder)
        return
    cache = io.load(tmp_path, folder)
    profile = cache.profiles[0]
    name = profile["details_file"]
    p = folder / name
    if change == "lazy_bytes":
        p.write_bytes(p.read_bytes() + b"UNIT_CHANGED")
    else:
        with gzip.open(p, "rt") as stream:
            data = json.load(stream)
        response = data["responses"][1]
        if change == "group":
            response["partitions"][0]["groups"][0]["infos"].pop()
        elif change == "cost":
            response["suffixes"][0]["panels"][0]["controls"][0]["costs"][0] += 0.01
        else:
            response["row_features"][0]["feature"] = "UNIT_WRONG_LOOKUP"
        p.write_bytes(gzip.compress(json.dumps(data).encode(), mtime=0))
        rehash(folder, name)
        cache = io.load(tmp_path, folder)
        profile = cache.profiles[0]
    with pytest.raises(ArithmeticError):
        cache.detail(profile)
