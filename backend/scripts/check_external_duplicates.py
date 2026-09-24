"""Create an exact/probable duplicate report from a prepared manifest."""
from __future__ import annotations

import argparse

try:
    from .external_validation_utils import duplicate_report, read_manifest, write_csv
except ImportError:
    from external_validation_utils import duplicate_report, read_manifest, write_csv


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows, missing = read_manifest(args.manifest)
    if missing:
        raise SystemExit(f"Manifest is missing columns: {', '.join(missing)}")
    write_csv(args.output, duplicate_report(rows), ["external_image_id", "duplicate_type"])
