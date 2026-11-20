"""Verify the preserved official failed hosted CI run and log bytes."""

import hashlib
import json
from pathlib import Path

folder = Path(__file__).resolve().parent
manifest = json.loads((folder / "manifest.json").read_bytes())
assert manifest["status"] == "hosted_source_qualification_failed"
listed = {row["file"]: row for row in manifest["files"]}
actual = {p.name for p in folder.iterdir() if p.is_file() and p.name != "manifest.json"}
assert set(listed) == actual
for name, expected in listed.items():
    raw = (folder / name).read_bytes()
    assert len(raw) == expected["bytes"]
    assert hashlib.sha256(raw).hexdigest() == expected["sha256"]
print(f"Verified {len(listed)} hosted-failure members")
