"""Freeze the prospective exact-turn comparison cohort once."""

from pathlib import Path

from turn_exact_transfer_selection import select

if __name__ == "__main__":
    select(Path(__file__).resolve().parents[1])
