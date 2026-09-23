#!/usr/bin/env python3
"""Create mechanical fingerprints for files.

Outputs path, size, mtime, and sha256. This script does not classify provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def fingerprint(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "exists": False}

    stat = path.stat()
    item = {
        "path": str(path),
        "exists": True,
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
        "size_bytes": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }

    if path.is_file():
        item["sha256"] = sha256_file(path)

    return item


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--indent", type=int, default=2)
    args = parser.parse_args()

    print(json.dumps([fingerprint(p) for p in args.paths], indent=args.indent, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
