"""Fixed whole-archive recall-cache comparison; read-only and source-gated."""

from pathlib import Path

from recall_cache_support import main

if __name__ == "__main__":
    raise SystemExit(main(Path(__file__).resolve().parents[1]))
