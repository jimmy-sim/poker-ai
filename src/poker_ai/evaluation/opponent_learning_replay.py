"""Read-only raw-book replay and source-bound own seat compositions."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from poker_ai.evaluation.averaging_history_artifacts import array_sha, decode_mass
from poker_ai.evaluation.averaging_history_math import window_mass
from poker_ai.evaluation.frozen_batch_replay import warm_mass as expected_warm
from poker_ai.evaluation.opponent_learning_contexts import Contexts
from poker_ai.evaluation.opponent_learning_design import WEIGHTS, Design, paired_work
from poker_ai.finite import FloatArray
from poker_ai.postflop.controlled_checkpoints import read_snapshot, write_snapshot
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline

ContextFor = Callable[[int], Contexts]
OUTER = {"file", "receipt", "metadata_sha256"}


def member(folder: Path, filename: Any) -> Path:
    if type(filename) is not str:
        raise ArithmeticError("own member needs a relative path")
    path = folder / filename
    if (
        Path(filename).is_absolute()
        or ".." in Path(filename).parts
        or not path.resolve().is_relative_to(folder.resolve())
    ):
        raise ArithmeticError("unsafe own member path")
    return path


def metadata(row: dict[str, Any]) -> dict[str, Any]:
    result = {k: v for k, v in row.items() if k not in OUTER}
    if sha(result) != row["metadata_sha256"]:
        raise ArithmeticError("own member metadata changed")
    return result


def raw_replay(
    folder: Path,
    design: Design,
    captures: list[dict[str, Any]],
    masses: list[dict[str, Any]],
    warms: list[dict[str, Any]],
    context_for: ContextFor,
    binding: str,
    deadline: Deadline,
) -> dict[str, FloatArray]:
    """Replay every raw policy/book, typed work crossing and exact normalization.

    This validates archived mathematics and provenance, not a fresh trajectory
    execution. Separate source/observer/oracle tests establish updater behavior;
    real ordinary controls must also match every original B4 work boundary.
    """
    design.require_rows("captures", captures)
    design.require_rows("masses", masses)
    if len(warms) != 30 or {r["path_index"] for r in warms} != set(range(30)):
        raise ArithmeticError("all thirty own warm origins required")
    warm_by_path = {r["path_index"]: r for r in warms}
    policies: dict[str, FloatArray] = {}
    books = {}
    rows = {r["id"]: r for r in captures}
    for index in range(30):
        path = design.path(index)
        context = context_for(path["coordinate"])
        tree = context.tree(path["tree_kind"])
        tree_sha = tree_digest(tree)
        warm = warm_by_path[index]
        if (
            any(not same(warm.get(k), v) for k, v in path.items())
            or warm["source_sha256"] != binding
            or warm["tree_sha256"] != tree_sha
            or type(warm["initialization_visits"]) is not int
            or warm["initialization_visits"] != 2 * len(tree.player)
        ):
            raise ArithmeticError("own warm game/source/work identity changed")
        metadata(warm)
        warm_mass = decode_mass(member(folder, warm["file"]).read_bytes(), tree, warm)
        if (
            warm["id"] != f"opponent-warm-{design.scope}-{index:02d}"
            or warm["origin"] != "own_simultaneous_uniform_warm_mass_both_books"
            or warm_mass.tobytes() != expected_warm(tree).tobytes()
        ):
            raise ArithmeticError(
                "own warm origin differs from exact uniform expectation"
            )
        for row in [r for r in captures + masses if r["path_index"] == index]:
            deadline.check()
            if row["source_sha256"] != binding or row["tree_sha256"] != tree_sha:
                raise ArithmeticError("raw member source or information view changed")
            metadata(row)
            paired_work([row], row["work_label"])
            if (
                row["initialization_visits"] != 2 * len(tree.player)
                or type(row["sampled_traversals"]) is not int
                or type(row["overshoot"]) is not int
                or row["sampled_traversals"] != 8 * (row["iteration"] - 1)
                or row["overshoot"] != row["total_work"] - row["work_label"]
                or row["warm_mass_sha256"] != warm["receipt"]["mass_sha256"]
            ):
                raise ArithmeticError(
                    "raw own initialization/traversal accounting changed"
                )
            for field in ("guard_sha256", "state_sha256", "current_sha256"):
                value = row[field]
                if (
                    type(value) is not str
                    or len(value) != 64
                    or any(c not in "0123456789abcdef" for c in value)
                ):
                    raise ArithmeticError(
                        "raw endpoint requires valid state fingerprints"
                    )
        for weight in WEIGHTS:
            previous = warm_mass
            for label in design.boundaries(index):
                wanted = design.mass(index, label, weight)
                selected = [r for r in masses if r["id"] == wanted["id"]]
                row = selected[0]
                mass = decode_mass(member(folder, row["file"]).read_bytes(), tree, row)
                window_mass(tree, previous, mass)
                books[index, label, weight] = (row, mass)
                previous = mass
        previous_work = 0
        previous_iteration = 0
        for label in design.boundaries(index):
            current_row = rows[design.raw(index, label, "current")["id"]]
            if (
                current_row["total_work"] < previous_work
                or current_row["iteration"] < previous_iteration
            ):
                raise ArithmeticError("raw work/iteration sequence moved backwards")
            previous_work = current_row["total_work"]
            previous_iteration = current_row["iteration"]
            shared = (
                "guard_sha256",
                "current_sha256",
                "initialization_visits",
                "previous_work",
                "total_work",
                "last_iteration_visits",
                "iteration",
                "sampled_traversals",
                "warm_mass_sha256",
            )
            for readout in ("current", "uniform_average", "linear_average"):
                row = rows[design.raw(index, label, readout)["id"]]
                if any(not same(row[k], current_row[k]) for k in shared):
                    raise ArithmeticError("readouts do not share one learning endpoint")
                policy = read_snapshot(
                    member(folder, row["file"]), tree, row["receipt"], metadata(row)
                )
                if readout == "current":
                    if array_sha(policy) != row["current_sha256"]:
                        raise ArithmeticError(
                            "current policy differs from captured endpoint"
                        )
                else:
                    weight = readout.removesuffix("_average")
                    mass_row, mass = books[index, label, weight]
                    if (
                        any(
                            not same(row[k], mass_row[k])
                            for k in (*shared, "state_sha256")
                        )
                        or tree.normalize(mass).tobytes() != policy.tobytes()
                    ):
                        raise ArithmeticError(
                            "average no longer matches its raw own ledger"
                        )
                policy.flags.writeable = False
                policies[row["id"]] = policy
        deadline.check()
    return policies


def compose_profiles(
    folder: Path,
    design: Design,
    captures: list[dict[str, Any]],
    policies: dict[str, FloatArray],
    context_for: ContextFor,
    binding: str,
    deadline: Deadline,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Write only108 new compositions; 108 whole-path arms alias existing data."""
    design.require_rows("captures", captures)
    source_rows = {r["id"]: r for r in captures}
    if set(policies) != set(source_rows):
        raise ArithmeticError("every checked raw policy required for composition")
    profiles = list(captures)
    arms = []
    for arm in design.manifest()["arms"]:
        deadline.check()
        sources = [source_rows[k] for k in arm["components"]]
        work = paired_work(sources, arm["work_label"])
        arm_row = dict(arm, charged_work=work)
        arms.append(arm_row)
        if arm["origin"] == "raw_alias":
            continue
        context = context_for(arm["coordinate"])
        values = [policies[k] for k in arm["components"]]
        if any(
            r["source_sha256"] != binding
            or array_sha(p) != r["receipt"]["policy_sha256"]
            for r, p in zip(sources, values, strict=True)
        ):
            raise ArithmeticError("composition differs from checked own raw sources")
        policy = context.combine(arm["arm"], values[0], values[1])
        meta = dict(
            **arm,
            source_sha256=binding,
            tree_sha256=tree_digest(context.coarse),
            charged_work=work,
            component_receipts=[r["receipt"] for r in sources],
            component_tree_sha256=[r["tree_sha256"] for r in sources],
        )
        filename = (
            f"composed/{arm['coordinate']}-{arm['work_label']}-"
            f"{arm['readout']}-{arm['arm']}.json.gz"
        )
        receipt = write_snapshot(folder / filename, context.coarse, policy, meta)
        profiles.append(
            dict(meta, file=filename, receipt=receipt, metadata_sha256=sha(meta))
        )
        policy.flags.writeable = False
        policies[arm["id"]] = policy
    design.require_rows("arms", arms)
    design.require_rows("profiles", profiles)
    return profiles, arms


def profile_replay(
    folder: Path,
    design: Design,
    captures: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    arms: list[dict[str, Any]],
    raw_policies: dict[str, FloatArray],
    context_for: ContextFor,
    binding: str,
    deadline: Deadline,
) -> dict[str, FloatArray]:
    """Reconstruct all108 compositions and216 logical arms without training."""
    for name, rows in (("captures", captures), ("profiles", profiles), ("arms", arms)):
        design.require_rows(name, rows)
    source_rows = {r["id"]: r for r in captures}
    by_id = {r["id"]: r for r in profiles}
    arm_rows = {r["id"]: r for r in arms}
    if set(raw_policies) != set(source_rows):
        raise ArithmeticError("complete checked raw policies required for replay")
    policies = dict(raw_policies)
    for row in captures:
        if not same(by_id[row["id"]], row):
            raise ArithmeticError("raw profile alias differs from captured source")
    for arm in design.manifest()["arms"]:
        deadline.check()
        sources = [source_rows[k] for k in arm["components"]]
        work = paired_work(sources, arm["work_label"])
        if not same(arm_rows[arm["id"]], dict(arm, charged_work=work)):
            raise ArithmeticError("logical arm changed its charged source work")
        if arm["origin"] == "raw_alias":
            continue
        context = context_for(arm["coordinate"])
        row = by_id[arm["id"]]
        expected = dict(
            **arm,
            source_sha256=binding,
            tree_sha256=tree_digest(context.coarse),
            charged_work=work,
            component_receipts=[r["receipt"] for r in sources],
            component_tree_sha256=[r["tree_sha256"] for r in sources],
        )
        if not same(metadata(row), expected):
            raise ArithmeticError(
                "composed policy source/role/compute metadata changed"
            )
        stored = read_snapshot(
            member(folder, row["file"]), context.coarse, row["receipt"], expected
        )
        rebuilt = context.combine(
            arm["arm"],
            raw_policies[arm["components"][0]],
            raw_policies[arm["components"][1]],
        )
        if stored.tobytes() != rebuilt.tobytes():
            raise ArithmeticError(
                "composed policy differs from its own seat projections"
            )
        stored.flags.writeable = False
        policies[row["id"]] = stored
    if set(policies) != set(by_id):
        raise ArithmeticError("all432 unique own profile objects must replay")
    return policies
