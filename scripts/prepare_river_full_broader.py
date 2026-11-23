"""Generate the prospectively fixed full-versus-B4 cohort once."""

from pathlib import Path

from river_full_broader_selection import select


def main() -> None:
    frozen = select(Path(__file__).resolve().parents[1])
    print(f"selected {len(frozen['spot_sha256'])} fixed structural inputs")
    print("Publish the cohort freeze before any outcome or profile.")


if __name__ == "__main__":
    main()
