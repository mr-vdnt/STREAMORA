"""
STREAMORA AI — Catalog Audit & Verification Tool

Scans data/raw/movies.csv and produces a comprehensive report of:
  - Synthetic/fake entries
  - Missing or invalid poster/backdrop URLs
  - Incomplete metadata (missing overview, cast, director, etc.)
  - Duplicated TMDB IDs
  - Placeholder text (Unknown, N/A in non-TV fields)

Exits with code 1 if ANY issues are found.
Run before ingest: python scripts/verify_catalog.py
"""

import os
import sys
import re
import pandas as pd

CSV_PATH = "data/raw/movies.csv"

TMDB_URL_RE = re.compile(
    r"^https://image\.tmdb\.org/t/p/(w500|w1280|original)/.+\.(jpg|png|jpeg)$"
)
SYNTHETIC_TITLE_RE = re.compile(r"\s+\d{2,}$")
SYNTHETIC_OVERVIEW_RE = re.compile(
    r"An extraordinary .+ production|A gripping .+ story that|"
    r"This .+ masterpiece explores|In this .+ tale"
)
PLACEHOLDER_RE = re.compile(
    r"^(Unknown|No overview available|N/A|None|Unavailable|TBD)$",
    re.IGNORECASE,
)
FAKE_TMDB_THRESHOLD = 100_000

REQUIRED_COLUMNS = [
    "item_id", "tmdb_id", "title", "genres", "overview",
    "cast", "director", "poster_url", "backdrop_url", "language", "content_type"
]

issues = []
warnings = []


def flag(msg: str, row_id=None, title=None):
    prefix = f"[FAIL]"
    if row_id is not None:
        prefix += f" item_id={row_id}"
    if title:
        prefix += f" '{title}'"
    issues.append(f"{prefix}: {msg}")


def warn(msg: str):
    warnings.append(f"[WARN]: {msg}")


def run():
    print("=" * 70)
    print(" STREAMORA — Catalog Verification Report")
    print("=" * 70)

    if not os.path.exists(CSV_PATH):
        print(f"\n[FAIL] {CSV_PATH} does not exist. Run build_verified_catalog.py first.")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)
    print(f"\nLoaded {len(df)} entries from {CSV_PATH}")

    # ── 1. Required column check ────────────────────────────────────────────
    print("\n[Check 1] Required columns...")
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        for col in missing_cols:
            flag(f"Missing required column: {col}")
    else:
        print(f"  OK — all {len(REQUIRED_COLUMNS)} required columns present")

    if missing_cols:
        print("\n[FAIL] Cannot continue — missing columns. Aborting.")
        _print_summary()
        sys.exit(1)

    # ── 2. Synthetic content detector ───────────────────────────────────────
    print("\n[Check 2] Synthetic/fake content detection...")
    synthetic_count = 0
    for _, row in df.iterrows():
        rid = row["item_id"]
        title = str(row["title"])
        tmdb_id = int(row.get("tmdb_id", 0))

        # tmdb_id of 0 means it was never assigned — certain fake
        if tmdb_id <= 0:
            flag(f"TMDB ID is 0 or missing (unassigned)", rid, title)
            synthetic_count += 1

        # Check for synthetic title suffixes (e.g., 'Whiplash 10') but ignore 4-digit years
        suffix_match = re.search(r"\s+(\d+)$", title)
        if suffix_match:
            suffix_num = suffix_match.group(1)
            # If it's a 4-digit year (like 2049 or 1917), it's likely a real title
            if not (len(suffix_num) == 4 and (suffix_num.startswith("19") or suffix_num.startswith("20"))):
                flag(f"Title looks generated (numeric suffix): '{title}'", rid)
                synthetic_count += 1

        overview = str(row.get("overview", ""))
        if SYNTHETIC_OVERVIEW_RE.search(overview):
            flag(f"Overview matches synthetic template", rid, title)
            synthetic_count += 1

    if synthetic_count == 0:
        print(f"  OK — no synthetic content detected")
    else:
        print(f"  FAIL — {synthetic_count} synthetic entry issues found")

    # ── 3. Artwork URL validation ────────────────────────────────────────────
    print("\n[Check 3] Artwork URL validation...")
    bad_poster = 0
    bad_backdrop = 0
    placeholder_img = 0
    for _, row in df.iterrows():
        rid = row["item_id"]
        title = str(row["title"])
        poster = str(row.get("poster_url", ""))
        backdrop = str(row.get("backdrop_url", ""))

        if "placehold" in poster or "placeholder" in poster:
            flag(f"poster_url is a placeholder image", rid, title)
            placeholder_img += 1
        elif not TMDB_URL_RE.match(poster):
            flag(f"poster_url invalid or not TMDB CDN: {poster[:60]}", rid, title)
            bad_poster += 1

        if "placehold" in backdrop or "placeholder" in backdrop:
            flag(f"backdrop_url is a placeholder image", rid, title)
            placeholder_img += 1
        elif not TMDB_URL_RE.match(backdrop):
            flag(f"backdrop_url invalid or not TMDB CDN: {backdrop[:60]}", rid, title)
            bad_backdrop += 1

    if bad_poster + bad_backdrop + placeholder_img == 0:
        print(f"  OK — all {len(df)} entries have valid TMDB CDN artwork URLs")
    else:
        print(f"  FAIL — {bad_poster} invalid posters, {bad_backdrop} invalid backdrops, {placeholder_img} placeholders")

    # ── 4. Metadata completeness ─────────────────────────────────────────────
    print("\n[Check 4] Metadata completeness...")
    placeholder_count = 0
    TV_TYPES = {"series", "anime", "documentary"}
    MOVIE_FIELDS = ["budget", "revenue", "box_office"]

    for _, row in df.iterrows():
        rid = row["item_id"]
        title = str(row["title"])
        ctype = str(row.get("content_type", "movie")).lower()

        # Check overview
        overview = str(row.get("overview", ""))
        if not overview or PLACEHOLDER_RE.match(overview.strip()):
            flag(f"Empty or placeholder overview", rid, title)
            placeholder_count += 1

        # Check director
        director = str(row.get("director", ""))
        if not director or PLACEHOLDER_RE.match(director.strip()):
            flag(f"Missing director", rid, title)
            placeholder_count += 1

        # Check cast
        cast = str(row.get("cast", ""))
        if not cast or PLACEHOLDER_RE.match(cast.strip()):
            flag(f"Missing cast", rid, title)
            placeholder_count += 1

        # For TV series only: check series-specific fields
        if ctype == 'series':
            if pd.isna(row.get("network")) or not str(row.get("network", "")).strip():
                warn(f"item_id={rid} '{title}': missing 'network' (TV series)")
            if pd.isna(row.get("seasons")) or str(row.get("seasons", "")).strip() in ("", "nan"):
                warn(f"item_id={rid} '{title}': missing 'seasons' (TV series)")

    if placeholder_count == 0:
        print(f"  OK — no placeholder metadata found")
    else:
        print(f"  FAIL — {placeholder_count} placeholder/empty metadata fields")

    # ── 5. Duplicate TMDB ID check ───────────────────────────────────────────
    print("\n[Check 5] Duplicate TMDB IDs...")
    dupes = df[df.duplicated(subset=["tmdb_id"], keep=False)]
    if len(dupes) > 0:
        for _, row in dupes.iterrows():
            flag(f"Duplicate tmdb_id={row['tmdb_id']}", row["item_id"], str(row["title"]))
        print(f"  FAIL — {len(dupes)} rows with duplicate TMDB IDs")
    else:
        print(f"  OK — all TMDB IDs are unique")

    # ── 6. Duplicate item_id check ───────────────────────────────────────────
    print("\n[Check 6] Duplicate item_IDs...")
    dupe_ids = df[df.duplicated(subset=["item_id"], keep=False)]
    if len(dupe_ids) > 0:
        for _, row in dupe_ids.iterrows():
            flag(f"Duplicate item_id={row['item_id']}", row["item_id"], str(row["title"]))
        print(f"  FAIL — {len(dupe_ids)} rows with duplicate item_IDs")
    else:
        print(f"  OK — all item_IDs are unique")

    # ── 7. Content-type distribution ─────────────────────────────────────────
    print("\n[Check 7] Content-type distribution...")
    if "content_type" in df.columns:
        counts = df["content_type"].value_counts()
        for ctype, count in counts.items():
            print(f"  {ctype}: {count}")
    else:
        warn("content_type column missing — cannot report distribution")

    _print_summary()


def _print_summary():
    print("\n" + "=" * 70)
    if warnings:
        print(f"\n[WARNINGS] ({len(warnings)} total):")
        for w in warnings:
            print(f"  {w}")

    if issues:
        print(f"\n[FAILED] {len(issues)} issue(s) detected:\n")
        for issue in issues:
            print(f"  {issue}")
        print(f"\n{'=' * 70}")
        print(f" VERIFICATION FAILED — Fix all issues before running ingest_catalog.py")
        print(f"{'=' * 70}\n")
        sys.exit(1)
    else:
        print(f"\n{'=' * 70}")
        print(f" VERIFICATION PASSED — Catalog is clean and ready for ingestion.")
        print(f" Total entries: {len(pd.read_csv(CSV_PATH))}")
        print(f"{'=' * 70}\n")
        sys.exit(0)


if __name__ == "__main__":
    run()
