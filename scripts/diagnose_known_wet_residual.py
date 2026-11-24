"""Run one preregistered read-only diagnosis of saved known-wet policies."""

import argparse
from pathlib import Path

from known_wet_residual.analysis import run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(Path.cwd(), args.output.resolve())


if __name__ == "__main__":
    main()
