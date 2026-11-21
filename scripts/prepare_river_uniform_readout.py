"""Generate the prospectively fixed uniform-readout cohort once."""

from pathlib import Path

from river_uniform_readout.selection import select


def main() -> None:
    frozen = select(Path(__file__).resolve().parents[1])
    print(f"selected {len(frozen['spot_sha256'])} fixed structural inputs")
    print("Publish the cohort freeze before any outcome or profile.")


if __name__ == "__main__":
    main()
