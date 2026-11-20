"""Run comparison-only OpenSpiel scalars after published own policies."""

import argparse
from pathlib import Path

from river_generalization.gate import (
    clean_revision,
    require_archive,
    source_fingerprint,
)
from river_generalization.learning import contract
from river_generalization.native import audit_all

from poker_ai.postflop.river_study import Deadline

SOURCE = Path("results/river-generalization/source-checks")
OWN = Path("results/river-generalization/own")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    contract(root)
    clean_revision(root)
    fingerprint = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    require_archive(root, root / OWN, "own_published", fingerprint)
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("retain existing native audit")
    audit_all(root, root / OWN, args.output.resolve(), Deadline(900))


if __name__ == "__main__":
    main()
