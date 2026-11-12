"""Own sampled state algebra, normalization and warm/post-warm support.

Replay authenticates saved tables/RNG/work receipts; it does not rerun millions
of random draws. The source-bound tiny proof tests the actual trajectory path.
No reference implementation is imported and no strategy is supplied to training.
"""

import copy
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.compact_full_context import Context, mass
from poker_ai.postflop.controlled_training import Rules, expected_pass
from poker_ai.postflop.frozen_batches import FrozenBatchTrainer, guard
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.toy.analysis import evaluate

FORMAT = "compact-sampled-state-v1"
WARM = "compact-sampled-warm-v1"
READOUTS = ("current", "uniform", "linear")


def integer(value: Any, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError("strict nonnegative integer counter required")
    return value


def table(tree: ArrayTree, values: FloatArray, *, signed: bool) -> list[list[float]]:
    if (
        values.dtype != np.float64
        or values.shape != tree.legal.shape
        or not np.isfinite(values).all()
        or np.any(values * (1 - tree.legal))
        or np.any(np.signbit(values) & (tree.legal == 0))
        or (not signed and np.any(values < 0))
    ):
        raise ValueError("finite legal float64 tables required")
    return [values[i, : len(menu)].tolist() for i, menu in enumerate(tree.actions)]


def unpack(tree: ArrayTree, rows: Any, *, signed: bool) -> FloatArray:
    if (
        not isinstance(rows, list)
        or len(rows) != len(tree.keys)
        or any(
            not isinstance(row, list)
            or len(row) != len(menu)
            or any(type(v) not in (int, float) for v in row)
            for row, menu in zip(rows, tree.actions, strict=True)
        )
    ):
        raise ValueError("all legal numeric rows required; booleans are not numbers")
    values = np.zeros_like(tree.legal)
    for i, row in enumerate(rows):
        values[i, : len(row)] = row
    table(tree, values, signed=signed)
    return values


def rng_state(saved: dict[str, Any]) -> Generator:
    if (
        set(saved) != {"bit_generator", "state", "has_uint32", "uinteger"}
        or saved["bit_generator"] != "PCG64"
        or set(saved["state"]) != {"state", "inc"}
        or integer(saved["has_uint32"]) not in (0, 1)
        or integer(saved["uinteger"]) >= 2**32
        or any(integer(saved["state"][k]) >= 2**128 for k in ("state", "inc"))
        or saved["state"]["inc"] % 2 != 1
    ):
        raise ValueError("canonical PCG64 state required")
    rng = Generator(PCG64(0))
    rng.bit_generator.state = copy.deepcopy(saved)
    if canonical(rng.bit_generator.state) != canonical(saved):
        raise ArithmeticError("RNG state changed during decoding")
    return rng


def warm_equations(tree: ArrayTree) -> tuple[FloatArray, FloatArray]:
    """Pure simultaneous uniform expectations; no learner/RNG/step is used."""
    policy = tree.normalize(tree.legal)
    regrets, averages = np.zeros_like(tree.legal), np.zeros_like(tree.legal)
    lookup = {key: i for i, key in enumerate(tree.keys)}
    for target in (0, 1):
        updates = expected_pass(tree, policy, target)
        for key, row in updates.regrets.items():
            regrets[lookup[key], : len(row)] += row
        for key, row in updates.averages.items():
            averages[lookup[key], : len(row)] += row
    return regrets, averages


def policies(
    tree: ArrayTree, regrets: FloatArray, uniform: FloatArray, linear: FloatArray
) -> dict[str, FloatArray]:
    for values, signed in ((regrets, True), (uniform, False), (linear, False)):
        table(tree, values, signed=signed)
    return dict(
        current=tree.normalize(np.maximum(regrets, 0)),
        uniform=tree.normalize(uniform),
        linear=tree.normalize(linear),
    )


def state_guard(
    tree: ArrayTree, saved: dict[str, Any], arrays: dict[str, FloatArray]
) -> str:
    """Rebuild the unchanged observer's state fingerprint without a learner."""
    selected = saved["sampled_rows"]
    if (
        not isinstance(selected, list)
        or len(selected) != len(tree.keys)
        or any(type(x) is not int or x not in (0, 1) for x in selected)
    ):
        raise ValueError("binary sampled-row mask required")
    current = policies(
        tree, arrays["regrets"], arrays["uniform_sum"], arrays["linear_sum"]
    )
    counters = {
        k: integer(saved[k])
        for k in (
            "iteration",
            "total_node_work",
            "initialization_work",
            "row_evaluations",
            "sampled_traversals",
        )
    }
    last = saved["last_pass_rows"]
    if (
        not isinstance(last, list)
        or len(last) != 2
        or any(integer(v) > len(tree.keys) for v in last)
    ):
        raise ValueError("invalid last-pass row counters")
    view = SimpleNamespace(
        tree=tree,
        regrets=arrays["regrets"],
        strategy_sum=arrays["linear_sum"],
        current_policy=current["current"],
        average_policy=current["linear"],
        uniform_sum=arrays["uniform_sum"],
        warm_sum=arrays["warm_sum"],
        rng=rng_state(saved["rng_state"]),
        sampled_keys={k for k, flag in zip(tree.keys, selected, strict=True) if flag},
        iteration=counters["iteration"],
        nodes_visited=counters["total_node_work"],
        initialization_visits=counters["initialization_work"],
        row_evaluations=counters["row_evaluations"],
        last_pass_rows=tuple(last),
        sampled_traversals=counters["sampled_traversals"],
        batch_size=4,
        rules=Rules("signed", "linear", "linear"),
        average_phase="opponent_pass",
        average_mass="chance_own_reach",
        traversal="external",
    )
    return guard(cast(FrozenBatchTrainer, view))


def validate_counters(tree: ArrayTree, saved: dict[str, Any], *, warm: bool) -> None:
    iteration = integer(saved["iteration"], 1)
    total = integer(saved["total_node_work"], 1)
    initial = integer(saved["initialization_work"], 1)
    traversals = integer(saved["sampled_traversals"])
    if (
        initial != 2 * len(tree.player)
        or traversals != 8 * (iteration - 1)
        or integer(saved["row_evaluations"]) < sum(saved["sampled_rows"])
    ):
        raise ArithmeticError("initialization/traversal work counters disagree")
    if warm:
        if (
            iteration != 1
            or total != initial
            or any(saved["sampled_rows"])
            or saved["row_evaluations"] != 0
            or saved["last_pass_rows"] != [0, 0]
        ):
            raise ArithmeticError("warm state contains sampled work")
    else:
        before = integer(saved["previous_node_work"], 1)
        last = integer(saved["last_iteration_work"], 1)
        label = integer(saved["work_checkpoint"], 1)
        if not (
            initial <= before < label <= total
            and total - before == last
            and last <= 8 * len(tree.player)
            and iteration >= 2
        ):
            raise ArithmeticError("not a first complete-iteration work crossing")


def decode(
    context: Context,
    saved: dict[str, Any],
    warm: dict[str, Any] | None,
    source_fingerprint: str,
    scope: str,
) -> tuple[dict[str, FloatArray], dict[str, FloatArray]]:
    tree = context.scoring.partition
    is_warm = warm is None
    expected_format = WARM if is_warm else FORMAT
    common = {
        "format",
        "scope",
        "source_fingerprint",
        "seed",
        "path_index",
        "binding",
        "iteration",
        "total_node_work",
        "initialization_work",
        "row_evaluations",
        "sampled_traversals",
        "last_pass_rows",
        "sampled_rows",
        "rng_state",
        "guard_sha256",
        "actions",
        "regrets",
        "uniform_sum",
        "linear_sum",
        "policies",
    }
    extra = (
        {"warm_sum"}
        if is_warm
        else {
            "previous_node_work",
            "last_iteration_work",
            "work_checkpoint",
            "warm_receipt",
        }
    )
    if (
        set(saved) != common | extra
        or saved["format"] != expected_format
        or scope not in ("software", "real")
        or saved["scope"] != scope
        or saved["source_fingerprint"] != source_fingerprint
        or canonical(saved["binding"]) != canonical(context.binding)
        or saved["actions"] != [list(a) for a in tree.actions]
        or integer(saved["path_index"]) >= 36
    ):
        raise ArithmeticError("sampled state schema/source/game/actions/scope changed")
    integer(saved["seed"], 1)
    arrays = {
        k: unpack(tree, saved[k], signed=k == "regrets")
        for k in ("regrets", "uniform_sum", "linear_sum")
    }
    if is_warm:
        arrays["warm_sum"] = unpack(tree, saved["warm_sum"], signed=False)
        expected_r, expected_a = warm_equations(tree)
        if (
            not np.array_equal(arrays["regrets"], expected_r)
            or any(
                not np.array_equal(arrays[k], expected_a)
                for k in ("warm_sum", "uniform_sum", "linear_sum")
            )
            or canonical(saved["rng_state"])
            != canonical(Generator(PCG64(saved["seed"])).bit_generator.state)
        ):
            raise ArithmeticError(
                "warm origin differs from simultaneous uniform equations"
            )
    else:
        assert warm is not None
        decode(context, warm, None, source_fingerprint, scope)
        if saved["seed"] != warm["seed"] or saved["path_index"] != warm["path_index"]:
            raise ArithmeticError("checkpoint belongs to a different warm path")
        arrays["warm_sum"] = unpack(tree, warm["warm_sum"], signed=False)
        if any(
            np.any(arrays[k] - arrays["warm_sum"] < 0)
            for k in ("uniform_sum", "linear_sum")
        ):
            raise ArithmeticError("cumulative average predates its warm origin")
    expected_policies = policies(
        tree, arrays["regrets"], arrays["uniform_sum"], arrays["linear_sum"]
    )
    if set(saved["policies"]) != set(READOUTS):
        raise ArithmeticError("all three policies required at the SAME crossing")
    for name in READOUTS:
        policy = unpack(tree, saved["policies"][name], signed=False)
        tree.validate_policy(policy)
        if not np.array_equal(policy, expected_policies[name]):
            raise ArithmeticError(
                "stored policy differs from its own table normalization"
            )
    validate_counters(tree, saved, warm=is_warm)
    if state_guard(tree, saved, arrays) != saved["guard_sha256"]:
        raise ArithmeticError("whole-state/RNG/book/observer fingerprint changed")
    return arrays, expected_policies


def scores(
    context: Context,
    saved: dict[str, Any],
    arrays: dict[str, FloatArray],
    profiles: dict[str, FloatArray],
) -> list[dict[str, Any]]:
    exact = context.scoring.exact
    mapping = context.scoring.exact_to_partition
    uniform = mass(exact, exact.normalize(exact.legal))
    masks = dict(
        all=np.ones(len(exact.keys), dtype=np.bool_),
        river=context.scoring.river_masks[0] | context.scoring.river_masks[1],
    )
    first = np.unique(mapping, return_index=True)[1]
    selected = np.array(saved["sampled_rows"], dtype=np.bool_)
    initialized = arrays["warm_sum"].sum(axis=1) > 0
    result = []
    for name in READOUTS:
        policy = profiles[name]
        expanded = context.scoring.expand(policy)
        evaluated = evaluate(exact, expanded)
        whole = (
            np.maximum(arrays["regrets"], 0)
            if name == "current"
            else arrays[name + "_sum"]
        )
        post = None if name == "current" else whole - arrays["warm_sum"]
        active = whole.sum(axis=1) > 0
        sampled = selected
        supports = dict(
            whole=active, initialized=initialized, sampled=sampled, fallback=~active
        )
        if post is not None:
            supports["post_warm"] = post.sum(axis=1) > 0
            supports["warm_only"] = initialized & ~supports["post_warm"]
        own = mass(exact, expanded)
        support: dict[str, Any] = {}
        for street, mask in masks.items():
            coarse = mask[first]
            entries: dict[str, Any] = dict(rows=int(coarse.sum()))
            for label, flags in supports.items():
                item: dict[str, Any] = dict(rows=int((flags & coarse).sum()))
                for reach_name, weights in (("uniform", uniform), ("own", own)):
                    denominator = float(weights[mask].sum())
                    item[reach_name + "_reach"] = (
                        float(
                            np.clip(
                                weights[mask] @ flags[mapping][mask] / denominator, 0, 1
                            )
                        )
                        if denominator > 0
                        else None
                    )
                entries[label] = item
            support[street] = entries
        result.append(
            dict(
                readout=name,
                value_player_zero_chips=evaluated.value_player_zero,
                best_response_zero_chips=evaluated.best_response_zero,
                best_response_one_chips=evaluated.best_response_one,
                exploitability_chips=evaluated.exploitability,
                exploitability_pot=evaluated.exploitability / context.pot,
                coverage=support["all"]["whole"]["uniform_reach"],
                support=support,
                support_basis="positive regrets"
                if name == "current"
                else "positive cumulative average mass",
            )
        )
    return result
