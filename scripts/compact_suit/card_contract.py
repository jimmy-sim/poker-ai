"""Own-only production dispatch proof; parser imports no reference modules.

The contract is part of the shared software command budget and own publication.
It supplies positive real card-dispatch coverage which the tiny signal games do
not have. These are deterministic software cases, not poker training outcomes.
"""

import copy
import json
from pathlib import Path
from typing import Any

import grouped_depth_support as fields
import suit_candidates_support as kernel

from compact_suit.contract import variant
from compact_suit.normalization import Normalization, validate
from poker_ai.postflop.river_study import Deadline, digest

NAME = "own-card-contract"
SCOPE = (
    "production dispatch software contract; own card outputs only; "
    "no native or training"
)


def member(root: Path, own_path: Path, own: dict[str, Any]) -> Path:
    meta = own["normalization_contract"]
    folder = own_path.parent / NAME
    if (
        folder.is_symlink()
        or not folder.resolve().is_relative_to(root.resolve())
        or meta["folder"] != NAME
        or meta["source_sha256"] != own["source_sha256"]
        or digest(folder / "contract.json") != meta["sha256"]
    ):
        raise ArithmeticError("own production-card proof member changed")
    verify(root, folder, own["source_sha256"])
    return folder


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        json.dumps(value, sort_keys=True, allow_nan=False).encode() + b"\n"
    )


def verify(root: Path, folder: Path, binding: str) -> dict[str, Any]:
    """Verify saved records and pinned own baselines, with no fresh evaluation."""
    saved: dict[str, Any] = json.loads((folder / "contract.json").read_text())
    c = variant(root)["normalization"]
    if (
        saved["scope"] != SCOPE
        or saved["status"] != "complete"
        or saved["source_sha256"] != binding
        or saved["poker_training_performed"] is not False
        or saved["reference_constructed"] is not False
        or saved["owner_before_unchanged"] is not True
        or saved["owner_after_unchanged"] is not True
        or type(saved["pid"]) is not int
        or type(saved["thread"]) is not int
        or saved.get("geometry_check_completed") is not True
        or canonical(saved.get("geometry_inventory"))
        != canonical(dict(table_entries=1248, geometry_slots=2704))
        or canonical(saved["valid_completed"])
        != canonical(dict(original=5724, reduced=5724))
    ):
        raise ArithmeticError("complete source-bound own card contract required")
    for name, expected in saved["raw_sha256"].items():
        path = folder / name
        if (
            path.is_symlink()
            or not path.resolve().is_relative_to(folder.resolve())
            or digest(path) != expected
        ):
            raise ArithmeticError("card-contract raw evidence changed")
    inventory = {str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file()}
    if inventory != {"contract.json", *saved["raw_sha256"]}:
        raise ArithmeticError("card-contract inventory changed")
    anchor_folder = root / "results/suit-candidates/software/child"
    anchor = json.loads((anchor_folder / "child.json").read_text())
    for name in ("card-inputs.json", "original-cards.jsonl", "fixed-results.json"):
        if digest(anchor_folder / name) != anchor["raw_sha256"][name]:
            raise ArithmeticError("pinned own card baseline changed")
    for name in ("card-inputs.json", "original-cards.jsonl"):
        if (folder / name).read_bytes() != (anchor_folder / name).read_bytes():
            raise ArithmeticError("fresh original card inputs or values changed")
    if (folder / "reduced-cards.jsonl").read_bytes() != (
        folder / "original-cards.jsonl"
    ).read_bytes():
        raise ArithmeticError("production dispatch differs from original card values")
    fixed = json.loads((folder / "fixed-results.json").read_text())
    old_fixed = json.loads((anchor_folder / "fixed-results.json").read_text())[
        "original"
    ]
    if (
        canonical(fixed) != canonical(dict(original=old_fixed, reduced=old_fixed))
        or len(old_fixed) != 17
    ):
        raise ArithmeticError("all seventeen production fixed behaviors required")
    required = {
        "card-inputs.json",
        "original-cards.jsonl",
        "reduced-cards.jsonl",
        "fixed-results.json",
        *(
            mode + "/" + name
            for mode in ("original", "reduced")
            for name in ("constructor.json", "constructor-events.jsonl")
        ),
        *("fixed/" + label + ".json" for label in old_fixed),
    }
    if set(saved["raw_sha256"]) != required:
        raise ArithmeticError("exact complete card-contract raw inventory required")
    for label, outcome in fixed["reduced"].items():
        state = json.loads((folder / "fixed" / (label + ".json")).read_text())
        failed = outcome["error"] is not None
        validate(
            state, c, parent=True, expected_errors=int(failed), expected_failure=failed
        )
        if (
            state["requests"] != 1
            or state["pid"] != saved["pid"]
            or state["thread"] != saved["thread"]
        ):
            raise ArithmeticError("fixed-case production dispatch identity changed")
    state = saved["normalization"]
    validate(state, c, parent=True)
    if (
        state["requests"] != 12296
        or state["reduced_evaluations"] != 12296
        or state["original_evaluations"] != 0
        or state["pid"] != saved["pid"]
        or state["thread"] != saved["thread"]
    ):
        raise ArithmeticError("complete positive production card coverage required")
    wanted = anchor["constructor_fingerprints"]["original"]
    for mode in ("original", "reduced"):
        vector = fields.read_constructors(
            folder / mode, "original", 1000, saved["pid"], saved["thread"]
        )
        if (
            len(vector) != 5
            or vector != wanted
            or vector != saved["constructors"][mode]
        ):
            raise ArithmeticError("all complete original constructor fields required")
    return saved


def collect(
    root: Path, folder: Path, binding: str, deadline: Deadline
) -> dict[str, Any]:
    """Called after six-role publication; public own evidence still precedes native."""
    # Parent-only imports: the saved-data parser above remains safe in workers.
    import compare_suit_candidates as fixture

    from poker_ai.abstraction import potential
    from poker_ai.abstraction.model import CardAbstraction
    from poker_ai.postflop.game import load_spot
    from poker_ai.postflop.matrix import MatrixTree
    from poker_ai.postflop.tree import SpotTree

    if folder.exists() or folder.is_symlink():
        raise FileExistsError("retain previous complete/partial card proof")
    folder.mkdir(parents=True)
    c = variant(root)["normalization"]
    contract = fixture.contract(root)
    saved: dict[str, Any] = dict(
        scope=SCOPE,
        status="starting",
        source_sha256=binding,
        poker_training_performed=False,
        reference_constructed=False,
        valid_completed={},
        constructors={},
        pid=__import__("os").getpid(),
        thread=__import__("threading").get_ident(),
    )
    write(folder / "contract.json", saved)
    try:
        kernel.check_geometry(c["lookup_table_sha256"], c["geometry_sha256"])
        saved.update(
            geometry_check_completed=True,
            geometry_inventory=dict(table_entries=1248, geometry_slots=2704),
        )
        cases = fixture.software_cases(contract)
        write(folder / "card-inputs.json", dict(cases=cases))
        tree = SpotTree.build(load_spot(root / contract["proof_spot"]))
        saved["owner_before_unchanged"] = potential.canonical_cards is kernel.BASE
        if not saved["owner_before_unchanged"]:
            raise ArithmeticError("unhooked own card baseline required")
        fixed: dict[str, Any] = {"original": {}, "reduced": {}}
        fixture.capture_cards(folder, cases, kernel.BASE, saved, "original")
        with fields.constructor_scope("original", folder / "original", 1000):
            model = CardAbstraction.load(root / contract["proof_model"])
            for encoding in contract["proof_encodings"]:
                deadline.check()
                MatrixTree.build(tree, encoding, model)
        for label in contract["software_fixed_calls"]:
            fixed["original"][label] = fixture.fixed_outcome(kernel.BASE, label)
        normalizer = Normalization(c, parent=True)
        with normalizer.installed():
            fixture.capture_cards(
                folder, cases, potential.canonical_cards, saved, "reduced"
            )
            with fields.constructor_scope("original", folder / "reduced", 1000):
                model = CardAbstraction.load(root / contract["proof_model"])
                for encoding in contract["proof_encodings"]:
                    deadline.check()
                    MatrixTree.build(tree, encoding, model)
        saved["normalization"] = normalizer.summary()
        for label in contract["software_fixed_calls"]:
            deadline.check()
            state = Normalization(c, parent=True)
            try:
                with state.installed():
                    args, kwargs = fixture.fixed_arguments(label)
                    before = copy.deepcopy((args, kwargs))
                    result = fixture.card_value(
                        potential.canonical_cards(*args, **kwargs)
                    )
            except (TypeError, ValueError) as error:
                result = dict(
                    value=None,
                    types=None,
                    error=dict(kind=type(error).__name__, message=str(error)),
                )
            finally:
                write(folder / "fixed" / (label + ".json"), state.summary())
            if (args, kwargs) != before:
                raise ArithmeticError("fixed production-card input changed")
            fixed["reduced"][label] = result
        write(folder / "fixed-results.json", fixed)
        for mode in ("original", "reduced"):
            saved["constructors"][mode] = fields.read_constructors(
                folder / mode, "original", 1000, saved["pid"], saved["thread"]
            )
        saved.update(
            status="complete",
            owner_after_unchanged=potential.canonical_cards is kernel.BASE,
        )
        saved["raw_sha256"] = {
            str(p.relative_to(folder)): digest(p)
            for p in sorted(folder.rglob("*"))
            if p.is_file() and p.name != "contract.json"
        }
        write(folder / "contract.json", saved)
        verify(root, folder, binding)
        deadline.check()
        return dict(
            folder=NAME, sha256=digest(folder / "contract.json"), source_sha256=binding
        )
    except BaseException as error:
        saved.update(status="failed_retained", failure_kind=type(error).__name__)
        try:
            write(folder / "contract.json", saved)
        except BaseException:
            pass  # Preserve the primary failure; retain prior partial bytes.
        raise
