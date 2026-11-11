"""Own mixed-information game views and checked coarse-policy composition.

This changes information grouping only. Fine inputs are legal acting-player
information sets, not omniscient hidden states. No trainer or reference solver
is constructed here, and no historical study admission is inherited.
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Any, TypeVar

import numpy as np

from poker_ai.finite import ArrayTree, FloatArray, IntArray
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.reply_trace import require_recall

VERSION = "own-opponent-views-v1"
ARRAYS = (
    "children",
    "valid",
    "player",
    "information",
    "owners",
    "legal",
    "chance_edges",
    "chance_reach",
    "terminal_values",
)
ArrayT = TypeVar("ArrayT", bound=np.ndarray[Any, Any])


def _frozen(values: ArrayT) -> ArrayT:
    result = values.copy()
    result.setflags(write=False)
    return result


def _array_digest(values: np.ndarray[Any, Any]) -> str:
    h = hashlib.sha256()
    h.update(json.dumps([values.dtype.str, values.shape]).encode())
    h.update(values.tobytes(order="C"))
    return h.hexdigest()


def tree_digest(tree: ArrayTree) -> str:
    """Bind exact finite game arrays, information groups and action labels."""
    payload = [
        tree.keys,
        tree.actions,
        [_array_digest(getattr(tree, n)) for n in ARRAYS],
        [_array_digest(level) for level in tree.levels],
    ]
    return hashlib.sha256(
        json.dumps(payload, separators=(",", ":")).encode()
    ).hexdigest()


def _tables(tree: ArrayTree) -> None:
    n = len(tree.keys)
    if (
        not n
        or len(set(tree.keys)) != n
        or len(tree.actions) != n
        or tree.owners.shape != (n,)
        or tree.legal.ndim != 2
        or tree.legal.shape[0] != n
        or any(type(k) is not str for k in tree.keys)
        or not np.isin(tree.owners, (0, 1)).all()
        or any(
            not menu
            or len(set(menu)) != len(menu)
            or any(type(a) is not int for a in menu)
            for menu in tree.actions
        )
    ):
        raise ValueError("valid unique information keys, owners and menus required")
    expected = np.zeros_like(tree.legal)
    for i, menu in enumerate(tree.actions):
        if len(menu) > tree.legal.shape[1]:
            raise ValueError("action menu exceeds legal width")
        expected[i, : len(menu)] = 1
    if not np.array_equal(expected, tree.legal):
        raise ValueError("legal columns must match declared action menus")
    for name in ARRAYS:
        array = getattr(tree, name)
        if array.dtype.kind not in "bif" or not np.isfinite(array).all():
            raise ValueError("finite numeric game arrays required")


@dataclass(frozen=True)
class OpponentView:
    tree: ArrayTree
    coarse_seat: int
    fine_to_view: IntArray
    coarse_own_to_view: IntArray
    fine_sha256: str
    coarse_sha256: str
    namespace: str
    sha256: str


def _view_digest(view: OpponentView) -> str:
    payload = [
        VERSION,
        view.coarse_seat,
        view.fine_sha256,
        view.coarse_sha256,
        view.namespace,
        tree_digest(view.tree),
        _array_digest(view.fine_to_view),
        _array_digest(view.coarse_own_to_view),
    ]
    return hashlib.sha256(
        json.dumps(payload, separators=(",", ":")).encode()
    ).hexdigest()


def _checked(view: OpponentView) -> None:
    if (
        type(view.coarse_seat) is not int
        or view.coarse_seat not in (0, 1)
        or _view_digest(view) != view.sha256
    ):
        raise ValueError("opponent view role/game/mapping changed")


def build_view(
    fine: ArrayTree, coarse: ArrayTree, fine_to_coarse: IntArray, coarse_seat: int
) -> OpponentView:
    """Keep the chosen seat's coarse groups and the other seat's fine groups.

    Inputs are already-built own finite game views. ScoringContext verifies
    identical topology/chance/payoffs, the full surjective mapping, menus/owners
    and equal-depth perfect recall. The output owns immutable array copies.
    """
    if type(coarse_seat) is not int or coarse_seat not in (0, 1):
        raise ValueError("coarse seat must be zero or one")
    _tables(fine)
    _tables(coarse)
    empty = np.zeros(len(fine.keys), dtype=np.bool_)
    ScoringContext(fine, coarse, fine_to_coarse, (empty, empty.copy()))
    fine_sha, coarse_sha = tree_digest(fine), tree_digest(coarse)
    namespace = hashlib.sha256(
        json.dumps([VERSION, fine_sha, coarse_sha, coarse_seat]).encode()
    ).hexdigest()
    keys: list[str] = []
    menus: list[tuple[int, ...]] = []
    owners: list[int] = []
    lookup: dict[str, int] = {}
    mapping = np.empty(len(fine.keys), dtype=np.int64)
    own = np.full(len(coarse.keys), -1, dtype=np.int64)
    for i in range(len(fine.keys)):
        is_coarse = fine.owners[i] == coarse_seat
        base = int(fine_to_coarse[i]) if is_coarse else i
        source = coarse if is_coarse else fine
        key = json.dumps(
            [VERSION, namespace, "coarse" if is_coarse else "fine", source.keys[base]],
            separators=(",", ":"),
        )
        if key not in lookup:
            lookup[key] = len(keys)
            keys.append(key)
            menus.append(source.actions[base])
            owners.append(int(source.owners[base]))
        mapping[i] = lookup[key]
        if is_coarse:
            own[base] = mapping[i]
    decision = fine.player >= 0
    information = np.full_like(fine.information, -1)
    information[decision] = mapping[fine.information[decision]]
    legal = np.zeros((len(keys), fine.legal.shape[1]), dtype=np.float64)
    for i, menu in enumerate(menus):
        legal[i, : len(menu)] = 1
    tree = ArrayTree(
        children=_frozen(fine.children),
        valid=_frozen(fine.valid),
        player=_frozen(fine.player),
        information=_frozen(information),
        keys=tuple(keys),
        actions=tuple(menus),
        owners=_frozen(np.array(owners, dtype=np.int64)),
        legal=_frozen(legal),
        chance_edges=_frozen(fine.chance_edges),
        chance_reach=_frozen(fine.chance_reach),
        terminal_values=_frozen(fine.terminal_values),
        levels=tuple(_frozen(v) for v in fine.levels),
    )
    require_recall(tree)
    draft = OpponentView(
        tree,
        coarse_seat,
        _frozen(mapping),
        _frozen(own),
        fine_sha,
        coarse_sha,
        namespace,
        "",
    )
    return OpponentView(
        tree,
        coarse_seat,
        draft.fine_to_view,
        draft.coarse_own_to_view,
        fine_sha,
        coarse_sha,
        namespace,
        _view_digest(draft),
    )


@dataclass(frozen=True)
class BoundViewPolicy:
    """In-memory view binding; training provenance belongs to the future runner."""

    view_sha256: str
    values: FloatArray
    sha256: str


def bind_policy(view: OpponentView, policy: FloatArray) -> BoundViewPolicy:
    _checked(view)
    view.tree.validate_policy(policy)
    values = _frozen(policy)
    return BoundViewPolicy(view.sha256, values, _array_digest(values))


def compose(
    coarse: ArrayTree,
    seat_zero: tuple[OpponentView, BoundViewPolicy],
    seat_one: tuple[OpponentView, BoundViewPolicy],
) -> FloatArray:
    """Project each own coarse seat from its own game; discard fine opponent rows.

    Both views must describe the same fine/coarse game and opposite coarse roles.
    No opponent policy row enters the returned coarse strategy table.
    """
    coarse_sha = tree_digest(coarse)
    result = np.zeros_like(coarse.legal)
    for target, (view, policy) in enumerate((seat_zero, seat_one)):
        _checked(view)
        if (
            view.coarse_seat != target
            or view.coarse_sha256 != coarse_sha
            or view.fine_sha256 != seat_zero[0].fine_sha256
            or policy.view_sha256 != view.sha256
            or policy.sha256 != _array_digest(policy.values)
        ):
            raise ValueError("policy source/game/role binding mismatch")
        view.tree.validate_policy(policy.values)
        owned = coarse.owners == target
        rows = view.coarse_own_to_view[owned]
        if np.any(rows < 0) or not np.all(view.tree.owners[rows] == target):
            raise ValueError("complete owned coarse projection required")
        result[owned] = policy.values[rows]
    coarse.validate_policy(result)
    return result
