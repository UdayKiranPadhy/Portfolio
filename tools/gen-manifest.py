#!/usr/bin/env python3
"""
Scans assets/images/{project,experience}/*/ for image files and rewrites
assets/images/manifest.json so the carousel picks them up automatically.

- Hand-written labels in the existing manifest are preserved.
- New files get an auto-generated label derived from the filename:
    "01-live-playground.png"  ->  "Live Playground"
    "training_curve.webp"     ->  "Training Curve"
- Files no longer present on disk are dropped from the manifest.
- Entries listed in the manifest that have no folder on disk are dropped too.

Usage:
    python3 tools/gen-manifest.py             # rewrite manifest from disk
    python3 tools/gen-manifest.py --dry-run   # show what would change, write nothing
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = ROOT / "assets" / "images"
MANIFEST_PATH = IMAGES_DIR / "manifest.json"
SUPPORTED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif"}
CATEGORIES = ("project", "experience")


def filename_to_label(filename: str) -> str:
    """01-live-playground.png -> 'Live Playground'."""
    stem = Path(filename).stem
    # strip a leading "NN-" or "NN_" ordering prefix
    stem = re.sub(r"^\d+[-_]", "", stem)
    # normalise separators to spaces
    words = re.split(r"[-_\s]+", stem)
    return " ".join(w.capitalize() for w in words if w)


def load_existing_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}
    try:
        return json.loads(MANIFEST_PATH.read_text())
    except json.JSONDecodeError as exc:
        sys.exit(f"manifest.json is invalid JSON: {exc}")


def scan_disk() -> dict[str, dict[str, list[str]]]:
    """Walk assets/images/{project,experience}/<id>/ and collect filenames."""
    out: dict[str, dict[str, list[str]]] = {c: {} for c in CATEGORIES}
    for category in CATEGORIES:
        cat_root = IMAGES_DIR / category
        if not cat_root.is_dir():
            continue
        for entry_dir in sorted(cat_root.iterdir()):
            if not entry_dir.is_dir():
                continue
            files = sorted(
                p.name
                for p in entry_dir.iterdir()
                if p.is_file() and p.suffix.lower() in SUPPORTED_EXT
            )
            if files:
                out[category][entry_dir.name] = files
    return out


def build_manifest(existing: dict, on_disk: dict) -> tuple[dict, list[str]]:
    """Merge: preserve hand-written labels, add new files, drop missing ones."""
    new_manifest: dict = {}
    # Preserve schema/docs block at top
    if "_schema" in existing:
        new_manifest["_schema"] = existing["_schema"]

    changes: list[str] = []

    for category in CATEGORIES:
        for entry_id, files_on_disk in on_disk[category].items():
            prior = existing.get(entry_id) or []
            prior_by_src = {item["src"]: item for item in prior if isinstance(item, dict) and "src" in item}

            merged: list[dict] = []
            for fname in files_on_disk:
                if fname in prior_by_src:
                    # Keep the existing label/order entry as-is
                    merged.append(prior_by_src[fname])
                else:
                    merged.append({"src": fname, "label": filename_to_label(fname)})
                    changes.append(f"  + {entry_id}: {fname} ({filename_to_label(fname)!r})")

            # Detect dropped files
            for src in prior_by_src:
                if src not in files_on_disk:
                    changes.append(f"  - {entry_id}: {src} (missing on disk)")

            new_manifest[entry_id] = merged

    # Detect entries entirely removed (in old manifest but no folder on disk)
    disk_ids = {eid for cat in CATEGORIES for eid in on_disk[cat]}
    for key in existing:
        if key == "_schema":
            continue
        if key not in disk_ids:
            changes.append(f"  - {key}: entire entry removed (no folder on disk)")

    return new_manifest, changes


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    existing = load_existing_manifest()
    on_disk = scan_disk()
    new_manifest, changes = build_manifest(existing, on_disk)

    if not changes:
        print("Manifest is already in sync with disk. No changes.")
        return

    print("Changes:")
    for line in changes:
        print(line)

    if dry_run:
        print("\n(dry-run; manifest not written)")
        return

    MANIFEST_PATH.write_text(json.dumps(new_manifest, indent=2) + "\n")
    print(f"\nWrote {MANIFEST_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
