"""Generate the prospectively fixed additional-spot cohort once."""

from pathlib import Path

from river_generalization.selection import select


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    frozen = select(root)
    print(f"selected {len(frozen['spot_sha256'])} fixed structural inputs")
    print("Publish the cohort freeze before any outcome or profile.")


if __name__ == "__main__":
    main()
