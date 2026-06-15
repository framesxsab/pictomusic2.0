"""Build the PictoMusic catalog from base, regional, and 2026 refresh datasets."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd


BASE_CATALOG = Path("Music_original_backup.csv")
OUTPUT_CATALOG = Path("Music.csv")
DATASETS_DIR = Path("datasets")

TARGET_COLS = [
    "name",
    "artist",
    "spotify_id",
    "preview",
    "img",
    "danceability",
    "energy",
    "loudness",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "acousticness_artist",
    "danceability_artist",
    "energy_artist",
    "instrumentalness_artist",
    "liveness_artist",
    "speechiness_artist",
    "valence_artist",
    "release_year",
    "release_date",
    "popularity",
    "duration_ms",
    "album_name",
    "album_type",
    "track_url",
    "catalog_year",
    "source",
]

AUDIO_FEATURES = [
    "danceability",
    "energy",
    "loudness",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
]

ARTIST_AGG_FEATURES = [
    "acousticness",
    "danceability",
    "energy",
    "instrumentalness",
    "liveness",
    "speechiness",
    "valence",
]

METADATA_COLUMNS = [
    "release_year",
    "release_date",
    "popularity",
    "duration_ms",
    "album_name",
    "album_type",
    "track_url",
    "catalog_year",
]

INDIAN_LANGS = {
    "Hindi",
    "Tamil",
    "Telugu",
    "Malayalam",
    "Punjabi",
    "Bengali",
    "Marathi",
    "Gujarati",
}


def first_existing(*paths: str) -> Path | None:
    for path in paths:
        candidate = Path(path)
        if candidate.exists():
            return candidate
    return None


def add_release_year(df: pd.DataFrame) -> pd.DataFrame:
    if "release_year" in df.columns:
        df["release_year"] = pd.to_numeric(df["release_year"], errors="coerce")
        return df
    if "year" in df.columns:
        df["release_year"] = pd.to_numeric(df["year"], errors="coerce")
    elif "release_date" in df.columns:
        df["release_year"] = pd.to_datetime(df["release_date"], errors="coerce").dt.year
    else:
        df["release_year"] = np.nan
    return df


def normalize_spotify_tracks(path: Path, source_prefix: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"  {path}: {len(df):,} total tracks")
    if "language" in df.columns:
        df = df[df["language"].isin(INDIAN_LANGS)].copy()
    print(f"  {path}: {len(df):,} Indian-language tracks")

    df = df.rename(
        columns={
            "track_name": "name",
            "artist_name": "artist",
            "track_id": "spotify_id",
            "artwork_url": "img",
            "year": "release_year",
        }
    )
    df["preview"] = ""
    df["catalog_year"] = 2026 if source_prefix.endswith("2026") else np.nan
    if "language" in df.columns:
        df["source"] = source_prefix + "_" + df["language"].astype(str)
    else:
        df["source"] = source_prefix
    return add_release_year(df)


def normalize_spotify_data_2026(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"  {path}: {len(df):,} tracks")
    df = df.rename(
        columns={
            "Song Name": "name",
            "Artists": "artist",
            "Released Dates": "release_date",
            "Popularity": "popularity",
            "Duration": "duration_ms",
            "Album Type": "album_type",
            "Cover Image": "img",
        }
    )
    df["spotify_id"] = ""
    df["preview"] = ""
    df["track_url"] = ""
    df["catalog_year"] = 2026
    df["source"] = "spotify_data_2026"
    return add_release_year(df)


def normalize_regional_datasets() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in sorted(DATASETS_DIR.glob("*_songs.csv")):
        lang = path.name.replace("_songs.csv", "")
        df = pd.read_csv(path)
        df = df.rename(
            columns={
                "song_name": "name",
                "singer": "artist",
                "singer_id": "spotify_id",
                "Valence": "valence",
            }
        )
        df["img"] = ""
        df["preview"] = ""
        df["source"] = f"regional_{lang}"
        df["release_year"] = np.nan
        df["release_date"] = ""
        df["popularity"] = np.nan
        df["catalog_year"] = np.nan
        frames.append(df)
        print(f"  {lang}: {len(df):,} songs")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def normalize_bollywood_2024(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"  Bollywood 2024: {len(df):,} tracks")
    df = df.rename(
        columns={
            "song_name": "name",
            "artist_name": "artist",
            "track_spotify_id": "spotify_id",
            "thumbnail_link": "img",
        }
    )
    df["preview"] = ""
    df["source"] = "bollywood_2024"
    df["release_year"] = 2024
    df["release_date"] = ""
    df["catalog_year"] = 2024
    return df


def standardize(df: pd.DataFrame, label: str) -> pd.DataFrame:
    df = df.copy()
    for col in TARGET_COLS:
        if col not in df.columns:
            df[col] = "" if col in {"name", "artist", "spotify_id", "preview", "img", "source"} else np.nan

    for col in AUDIO_FEATURES + ["popularity", "duration_ms", "release_year", "catalog_year"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    result = df[TARGET_COLS].copy()
    has_ids = result["spotify_id"].fillna("").astype(str).str.strip().ne("").sum()
    print(f"  {label}: {len(result):,} rows, {has_ids:,} with spotify_id")
    return result


def deduplicate(combined: pd.DataFrame) -> pd.DataFrame:
    combined = combined.copy()
    combined["name"] = combined["name"].fillna("").astype(str).str.strip()
    combined["artist"] = combined["artist"].fillna("").astype(str).str.strip()
    combined["spotify_id"] = combined["spotify_id"].fillna("").astype(str).str.strip()

    combined = combined[
        (combined["name"] != "")
        & (combined["name"].str.lower() != "nan")
        & (combined["artist"] != "")
        & (combined["artist"].str.lower() != "nan")
    ]
    print(f"  After cleaning empty rows: {len(combined):,}")

    combined["has_preview"] = combined["preview"].astype(str).str.startswith("http").astype(int)
    combined["has_img"] = combined["img"].astype(str).str.startswith("http").astype(int)
    combined["release_year_num"] = pd.to_numeric(combined["release_year"], errors="coerce").fillna(0)
    combined["popularity_num"] = pd.to_numeric(combined["popularity"], errors="coerce").fillna(0)
    combined["richness"] = combined["has_preview"] + combined["has_img"]
    combined = combined.sort_values(
        ["richness", "release_year_num", "popularity_num"],
        ascending=[False, False, False],
    )

    valid_ids = combined["spotify_id"].notna() & combined["spotify_id"].ne("") & combined["spotify_id"].ne("nan")
    with_id = combined[valid_ids].drop_duplicates(subset=["spotify_id"], keep="first")
    no_id = combined[~valid_ids].drop_duplicates(subset=["name", "artist"], keep="first")
    result = pd.concat([with_id, no_id], ignore_index=True)
    return result.drop(columns=["has_preview", "has_img", "release_year_num", "popularity_num", "richness"])


def add_artist_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    for col in ARTIST_AGG_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    artist_agg = df.groupby("artist")[ARTIST_AGG_FEATURES].mean()
    artist_agg.columns = [f"{col}_artist" for col in ARTIST_AGG_FEATURES]
    artist_agg = artist_agg.reset_index()

    for col in [f"{c}_artist" for c in ARTIST_AGG_FEATURES]:
        if col in df.columns:
            df = df.drop(columns=[col])
    return df.merge(artist_agg, on="artist", how="left")


def main() -> None:
    print("=" * 60)
    print("PICTOMUSIC 2026 - Pan-Indian Dataset Merge")
    print("=" * 60)

    base_catalog = BASE_CATALOG if BASE_CATALOG.exists() else OUTPUT_CATALOG
    print(f"\n[1/6] Loading base catalog: {base_catalog}")
    existing = pd.read_csv(base_catalog)
    existing["source"] = "original"

    print("\n[2/6] Processing Spotify refresh datasets")
    spotify_tracks_path = first_existing("spotify_tracks.csv", "datasets/spotify_tracks.csv")
    spotify_tracks = (
        normalize_spotify_tracks(spotify_tracks_path, "spotify_tracks_2026")
        if spotify_tracks_path
        else pd.DataFrame()
    )
    spotify_data_path = first_existing("spotify_data.csv")
    spotify_data = normalize_spotify_data_2026(spotify_data_path) if spotify_data_path else pd.DataFrame()

    print("\n[3/6] Processing regional language datasets")
    regional = normalize_regional_datasets()

    print("\n[4/6] Processing Bollywood 2024 dataset")
    bollywood_path = first_existing("data.csv", "datasets/data.csv")
    bollywood = normalize_bollywood_2024(bollywood_path) if bollywood_path else pd.DataFrame()

    print("\n[5/6] Standardizing and deduplicating")
    frames = [
        standardize(existing, "Original catalog"),
        standardize(spotify_tracks, "Spotify tracks 2026"),
        standardize(spotify_data, "Spotify data 2026"),
        standardize(regional, "Regional languages"),
        standardize(bollywood, "Bollywood 2024"),
    ]
    combined = pd.concat(frames, ignore_index=True)
    print(f"  Combined before deduplication: {len(combined):,}")
    combined = deduplicate(combined)
    print(f"  After deduplication: {len(combined):,}")

    print("\n[6/6] Computing artist aggregates and saving")
    combined = add_artist_aggregates(combined)
    for col in TARGET_COLS:
        if col not in combined.columns:
            combined[col] = "" if col in {"name", "artist", "spotify_id", "preview", "img", "source"} else np.nan
    combined = combined[TARGET_COLS]

    if not BASE_CATALOG.exists() and OUTPUT_CATALOG.exists():
        os.rename(OUTPUT_CATALOG, BASE_CATALOG)
        print(f"  Backed up original catalog as {BASE_CATALOG}")

    combined.to_csv(OUTPUT_CATALOG, index=False)
    print(f"\n  SAVED: {OUTPUT_CATALOG} ({len(combined):,} songs)")
    print("\nSummary by source:")
    for source, count in combined["source"].value_counts().items():
        print(f"  {source}: {count:,}")
    previews = combined["preview"].astype(str).str.startswith("http").sum()
    artwork = combined["img"].astype(str).str.startswith("http").sum()
    recent = pd.to_numeric(combined["release_year"], errors="coerce").ge(2025).sum()
    refreshed = pd.to_numeric(combined["catalog_year"], errors="coerce").ge(2026).sum()
    print(f"\n  Songs with preview URL: {previews:,} ({100 * previews / len(combined):.1f}%)")
    print(f"  Songs with artwork: {artwork:,} ({100 * artwork / len(combined):.1f}%)")
    print(f"  2025+ songs: {recent:,} ({100 * recent / len(combined):.1f}%)")
    print(f"  2026 refresh rows: {refreshed:,} ({100 * refreshed / len(combined):.1f}%)")
    print("\n[IMPORTANT] Regenerate song_embeddings_fp16.npy after this merge.")


if __name__ == "__main__":
    main()
