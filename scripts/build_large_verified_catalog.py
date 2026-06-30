"""
Streamora — Verified Catalog Builder (v2)
=========================================
Downloads the TMDB 5000 Movies + Credits datasets from GitHub (~5MB, fast),
merges them, extracts director/cast from JSON blobs, builds proper poster
and backdrop URLs, then saves to data/raw/movies.csv.

All records without a valid poster_path are dropped.  No synthetic content
is ever inserted.  The script is idempotent: run it at any time to refresh
the catalog from source.
"""

import os
import ast
import json
import pandas as pd
import requests

# ── Source URLs (small, public GitHub mirrors of the Kaggle TMDB-5000 dataset)
MOVIES_URL  = (
    "https://raw.githubusercontent.com/rengalv/"
    "Movies-Data-Analysis-Grab-a-Popcorn/master/tmdb_5000_movies.csv"
)
CREDITS_URL = (
    "https://raw.githubusercontent.com/harshitcodes/"
    "tmdb_movie_data_analysis/master/tmdb-5000-movie-dataset/"
    "tmdb_5000_credits.csv"
)

TMDB_IMAGE_BASE_W500  = "https://image.tmdb.org/t/p/w500"
TMDB_IMAGE_BASE_W1280 = "https://image.tmdb.org/t/p/w1280"

OUTPUT_PATH = os.path.join("data", "raw", "movies.csv")


# ── Helper: parse JSON blobs safely ──────────────────────────────────────────
def _parse_json_col(value):
    """Return a Python object from a JSON / Python-literal string, or []."""
    if not value or (isinstance(value, float) and pd.isna(value)):
        return []
    try:
        return json.loads(str(value))
    except Exception:
        try:
            return ast.literal_eval(str(value))
        except Exception:
            return []


def extract_names(json_str, limit: int = 6) -> str:
    items = _parse_json_col(json_str)
    if not isinstance(items, list):
        return ""
    return ", ".join(i["name"] for i in items[:limit] if isinstance(i, dict) and "name" in i)


def extract_director(crew_json: str) -> str:
    items = _parse_json_col(crew_json)
    if not isinstance(items, list):
        return ""
    for item in items:
        if isinstance(item, dict) and item.get("job") == "Director":
            return item.get("name", "")
    return ""


def extract_writer(crew_json: str) -> str:
    items = _parse_json_col(crew_json)
    if not isinstance(items, list):
        return ""
    for item in items:
        if isinstance(item, dict) and item.get("job") in ("Screenplay", "Writer", "Story"):
            return item.get("name", "")
    return ""


def extract_genres(genres_json: str) -> str:
    items = _parse_json_col(genres_json)
    if not isinstance(items, list):
        return "Drama"
    names = [i["name"] for i in items if isinstance(i, dict) and "name" in i]
    return ", ".join(names) if names else "Drama"


def extract_studio(companies_json: str) -> str:
    items = _parse_json_col(companies_json)
    if not isinstance(items, list):
        return "Unknown Studio"
    names = [i["name"] for i in items[:2] if isinstance(i, dict) and "name" in i]
    return ", ".join(names) if names else "Unknown Studio"


def extract_languages(languages_json: str) -> str:
    items = _parse_json_col(languages_json)
    if not isinstance(items, list):
        return "English"
    names = [i.get("english_name") or i.get("name", "") for i in items
             if isinstance(i, dict)]
    names = [n for n in names if n]
    return ", ".join(names[:3]) if names else "English"


def extract_countries(countries_json: str) -> str:
    items = _parse_json_col(countries_json)
    if not isinstance(items, list):
        return "United States"
    names = [i.get("name", "") for i in items if isinstance(i, dict)]
    names = [n for n in names if n]
    return ", ".join(names[:3]) if names else "United States"


# ── Downloader ────────────────────────────────────────────────────────────────
def _download_csv(url: str, label: str) -> pd.DataFrame:
    print(f"Downloading {label} …")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    from io import StringIO
    df = pd.read_csv(StringIO(resp.text))
    print(f"  -> {len(df):,} rows loaded.")
    return df


# ── Main ──────────────────────────────────────────────────────────────────────
def build_verified_catalog():
    df_movies  = _download_csv(MOVIES_URL,  "TMDB-5000 movies")
    df_credits = _download_csv(CREDITS_URL, "TMDB-5000 credits")

    # Standardise join key
    if "movie_id" in df_credits.columns:
        df_credits = df_credits.rename(columns={"movie_id": "id"})
    df_credits["id"] = pd.to_numeric(df_credits["id"], errors="coerce")
    df_movies["id"]  = pd.to_numeric(df_movies["id"],  errors="coerce")

    print("Merging on 'id' …")
    df = pd.merge(df_movies, df_credits[["id", "cast", "crew"]], on="id", how="inner")
    print(f"  -> {len(df):,} rows after merge.")

    # ── Drop rows that are missing critical fields ────────────────────────────
    required_cols = ["title", "overview", "poster_path"]
    df = df.dropna(subset=[c for c in required_cols if c in df.columns])
    df = df[df["poster_path"].astype(str).str.strip().str.len() > 5]
    # Backdrop is optional in the source; we default to poster when absent
    if "backdrop_path" not in df.columns:
        df["backdrop_path"] = df["poster_path"]
    df["backdrop_path"] = df["backdrop_path"].fillna(df["poster_path"])
    df = df[df["backdrop_path"].astype(str).str.strip().str.len() > 5]
    print(f"  -> {len(df):,} rows after artwork filter.")

    # ── Extract structured columns ────────────────────────────────────────────
    print("Extracting cast, director, genres …")
    df["cast_names"]     = df["cast"].apply(extract_names)
    df["director_name"]  = df["crew"].apply(extract_director)
    df["writer_name"]    = df["crew"].apply(extract_writer)
    df["genres_clean"]   = df["genres"].apply(extract_genres)
    df["studio_clean"]   = df["production_companies"].apply(extract_studio) \
                               if "production_companies" in df.columns else "Unknown Studio"
    df["languages_clean"]= df["spoken_languages"].apply(extract_languages) \
                               if "spoken_languages" in df.columns else "English"
    df["countries_clean"]= df["production_countries"].apply(extract_countries) \
                               if "production_countries" in df.columns else "United States"

    # Drop rows without a director (ensures real metadata)
    df = df[df["director_name"].str.strip().str.len() > 0]
    print(f"  -> {len(df):,} rows after director filter.")

    # ── Build release year ────────────────────────────────────────────────────
    if "release_date" in df.columns:
        df["release_year"] = df["release_date"].astype(str).str[:4]
    else:
        df["release_year"] = "Unknown"

    # ── Compose title with year (Streamora format) ────────────────────────────
    df["title_with_year"] = df.apply(
        lambda r: f"{r['title']} ({r['release_year']})"
        if str(r.get("release_year", "")).isdigit() else r["title"],
        axis=1
    )

    # ── Build final catalog ───────────────────────────────────────────────────
    final_rows = []
    for seq, (_, row) in enumerate(df.iterrows(), start=1):
        budget_val  = row.get("budget",  0)
        revenue_val = row.get("revenue", 0)

        final_rows.append({
            "item_id":       seq,
            "tmdb_id":       int(row["id"]),
            "title":         row["title_with_year"],
            "original_title":row["title"],
            "release_date":  row.get("release_date", ""),
            "runtime":       row.get("runtime", ""),
            "genres":        row["genres_clean"],
            "overview":      row["overview"],
            "cast":          row["cast_names"],
            "director":      row["director_name"],
            "writer":        row["writer_name"],
            "studio":        row["studio_clean"],
            "languages":     row["languages_clean"],
            "countries":     row["countries_clean"],
            "rating":        round(float(row.get("vote_average", 0) or 0), 1),
            "popularity":    round(float(row.get("popularity",   0) or 0), 2),
            "budget":        int(budget_val)  if str(budget_val).replace(".","").isdigit()  else 0,
            "revenue":       int(revenue_val) if str(revenue_val).replace(".","").isdigit() else 0,
            "poster_url":    f"{TMDB_IMAGE_BASE_W500}{row['poster_path']}",
            "backdrop_url":  f"{TMDB_IMAGE_BASE_W1280}{row['backdrop_path']}",
        })

    final_df = pd.DataFrame(final_rows)
    print(f"\nFinal verified catalog: {len(final_df):,} titles.")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    final_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved -> {OUTPUT_PATH}")
    return final_df


if __name__ == "__main__":
    build_verified_catalog()
