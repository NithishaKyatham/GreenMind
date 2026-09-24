"""Build a hash-enriched manifest from an authorized local image directory.

This script does not assign taxonomy mappings. Supply those in the source CSV;
blank or unknown metadata stays blank.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
    from .external_validation_utils import average_hash, sha256_file, write_csv
except ImportError:
    from external_validation_utils import average_hash, sha256_file, write_csv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--image-root", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--perceptual-hash", action="store_true")
    args = parser.parse_args()

    root = Path(args.image_root).resolve()
    with Path(args.input_csv).open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0].keys()) if rows else []
    for row in rows:
        path = (root / row.get("local_relative_path", "")).resolve()
        try:
            path.relative_to(root)
            row["sha256"] = sha256_file(path)
            row["perceptual_hash"] = average_hash(path) if args.perceptual_hash else row.get("perceptual_hash", "")
            row["exclusion_reason"] = row.get("exclusion_reason", "")
        except (ValueError, FileNotFoundError, OSError) as exc:
            row["sha256"] = ""
            row["perceptual_hash"] = ""
            row["exclusion_reason"] = f"image_unavailable_or_unsafe: {exc}"
    if not fields:
        fields = sorted({key for row in rows for key in row})
    for required in ("sha256", "perceptual_hash", "exclusion_reason"):
        if required not in fields:
            fields.append(required)
    write_csv(args.output_csv, rows, fields)


if __name__ == "__main__":
    main()
