"""
PictoMusic Preprocessing Pipeline
Dataset loading, tagging, cleaning, and enhanced description building.
Handles the merged Music.csv (91K+ songs with source column from multiple Indian datasets).
"""

import argparse
import logging
import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from config import (
    AUDIO_FEATURE_COLUMNS,
    DATASET_PATH,
    FEATURE_DESCRIPTORS,
    INDIAN_ARTIST_HINTS,
    INDIAN_TITLE_HINTS,
    LANGUAGE_DISPLAY_MAP,
    MOOD_THRESHOLDS,
)
from ranking import build_india_affinity, parse_release_year

logger = logging.getLogger(__name__)

# Mapping from source column values to (language, genre, region)
SOURCE_TAG_MAP = {
    "original":            ("en", "pop",       "western"),
    "spotify_tracks":      ("hi", "bollywood", "bollywood"),
    "spotify_tracks_Hindi": ("hi", "bollywood", "bollywood"),
    "spotify_tracks_Tamil": ("ta", "tamil",     "south_indian"),
    "spotify_tracks_Telugu": ("te", "telugu",   "south_indian"),
    "spotify_tracks_Malayalam": ("ml", "malayalam", "south_indian"),
    "spotify_tracks_2026_Hindi": ("hi", "bollywood", "bollywood"),
    "spotify_tracks_2026_Tamil": ("ta", "tamil",     "south_indian"),
    "spotify_tracks_2026_Telugu": ("te", "telugu",   "south_indian"),
    "spotify_tracks_2026_Malayalam": ("ml", "malayalam", "south_indian"),
    "spotify_tracks_2026_Punjabi": ("pa", "punjabi", "punjabi"),
    "spotify_tracks_2026_Bengali": ("bn", "bengali", "bengali"),
    "spotify_tracks_2026_Marathi": ("mr", "marathi", "marathi"),
    "spotify_tracks_2026_Gujarati": ("gu", "gujarati", "gujarati"),
    "spotify_data_2026":   ("hi", "bollywood", "bollywood"),
    "bollywood_2024":      ("hi", "bollywood", "bollywood"),
    "regional_Hindi":      ("hi", "hindi",     "bollywood"),
    "regional_Tamil":      ("ta", "tamil",     "south_indian"),
    "regional_Telugu":     ("te", "telugu",    "south_indian"),
    "regional_Kannada":    ("kn", "kannada",   "south_indian"),
    "regional_Malayalam":  ("ml", "malayalam", "south_indian"),
    "regional_Punjabi":    ("pa", "punjabi",   "punjabi"),
    "regional_Bengali":    ("bn", "bengali",   "bengali"),
    "regional_Marathi":    ("mr", "marathi",   "marathi"),
    "regional_Gujarati":   ("gu", "gujarati",  "gujarati"),
    "regional_Urdu":       ("ur", "urdu",      "bollywood"),
    "regional_Odia":       ("or", "odia",      "odia"),
    "regional_Assamese":   ("as", "assamese",  "northeast_indian"),
    "regional_Rajasthani": ("hi", "folk",      "rajasthani"),
    "regional_Bhojpuri":   ("bh", "bhojpuri",  "bhojpuri"),
    "regional_Haryanvi":   ("hi", "haryanvi",  "haryanvi"),
    "regional_Old":        ("hi", "retro",     "bollywood"),
}

LANGUAGE_ALIASES = {
    "hindi": "hi",
    "tamil": "ta",
    "telugu": "te",
    "punjabi": "pa",
    "bengali": "bn",
    "kannada": "kn",
    "malayalam": "ml",
    "marathi": "mr",
    "urdu": "ur",
    "sanskrit": "sa",
    "bhojpuri": "bh",
    "assamese": "as",
    "gujarati": "gu",
    "odia": "or",
    "oriya": "or",
    "english": "en",
}

INDIAN_ARTIST_DEFAULT_TAGS = {
    "arijit singh": ("hi", "bollywood", "bollywood"),
    "pritam": ("hi", "bollywood", "bollywood"),
    "anirudh": ("ta", "tamil", "south_indian"),
    "anirudh ravichander": ("ta", "tamil", "south_indian"),
    "a r rahman": ("ta", "filmi", "south_indian"),
    "a.r. rahman": ("ta", "filmi", "south_indian"),
    "diljit dosanjh": ("pa", "punjabi", "punjabi"),
    "ap dhillon": ("pa", "punjabi", "punjabi"),
    "shubh": ("pa", "punjabi", "punjabi"),
    "karan aujla": ("pa", "punjabi", "punjabi"),
    "guru randhawa": ("pa", "punjabi", "punjabi"),
    "ammy virk": ("pa", "punjabi", "punjabi"),
    "jass manak": ("pa", "punjabi", "punjabi"),
    "harrdy sandhu": ("pa", "punjabi", "punjabi"),
    "amrit maan": ("pa", "punjabi", "punjabi"),
    "mankirt aulakh": ("pa", "punjabi", "punjabi"),
    "b praak": ("pa", "punjabi", "punjabi"),
    "pawan singh": ("bh", "bhojpuri", "bhojpuri"),
    "khesari lal yadav": ("bh", "bhojpuri", "bhojpuri"),
    "antra singh priyanka": ("bh", "bhojpuri", "bhojpuri"),
    "bharat sharma vyas": ("bh", "bhojpuri", "bhojpuri"),
    "sharda sinha": ("bh", "bhojpuri", "bhojpuri"),
}

TITLE_TAG_OVERRIDES = {
    "bhojpuri": ("bh", "bhojpuri", "bhojpuri"),
    "chhath": ("bh", "bhojpuri", "bhojpuri"),
    "garba": ("gu", "gujarati", "gujarati"),
    "bhangra": ("pa", "punjabi", "punjabi"),
    "gidda": ("pa", "punjabi", "punjabi"),
}


def contains_title_hint(title: str, hints: set[str]) -> bool:
    """Match Indian title hints as words, not arbitrary English substrings."""
    return any(re.search(rf"\b{re.escape(hint)}\b", title) for hint in hints)


def load_dataset(path: str) -> pd.DataFrame:
    """Load the merged Music.csv dataset."""
    df = pd.read_csv(path, low_memory=False)
    logger.info("Loaded dataset: %d songs from %s", len(df), path)
    return df


def infer_tags_from_source(df: pd.DataFrame) -> pd.DataFrame:
    """Add language, genre, and region columns based on the source column."""
    df = df.copy()

    if "source" not in df.columns:
        df["source"] = "original"

    languages = []
    genres = []
    regions = []

    for _, row in df.iterrows():
        source = row.get("source", "original")
        source_str = str(source).strip()
        lang, genre, region = SOURCE_TAG_MAP.get(source_str, ("en", "pop", "western"))

        artist = str(row.get("artist", "")).lower()
        title = str(row.get("name", "")).lower()

        for artist_hint, inferred in INDIAN_ARTIST_DEFAULT_TAGS.items():
            if artist_hint in artist:
                lang, genre, region = inferred
                break

        for title_hint, inferred in TITLE_TAG_OVERRIDES.items():
            if title_hint in title:
                lang, genre, region = inferred
                break

        if lang == "en":
            if contains_title_hint(title, INDIAN_TITLE_HINTS):
                lang, genre, region = "hi", "bollywood", "bollywood"

        languages.append(lang)
        genres.append(genre)
        regions.append(region)

    if "language" not in df.columns:
        df["language"] = languages
    else:
        normalized = df["language"].fillna("").astype(str).str.strip().str.lower()
        df["language"] = normalized.map(LANGUAGE_ALIASES).fillna(normalized)
        df.loc[df["language"].isin(["", "nan", "none"]), "language"] = pd.Series(languages, index=df.index)

    if "genre" not in df.columns:
        df["genre"] = genres
    else:
        df["genre"] = df["genre"].fillna("").astype(str).str.strip().str.lower()
        df.loc[df["genre"].isin(["", "nan", "none"]), "genre"] = pd.Series(genres, index=df.index)

    if "region" not in df.columns:
        df["region"] = regions
    else:
        df["region"] = df["region"].fillna("").astype(str).str.strip().str.lower()
        df.loc[df["region"].isin(["", "nan", "none"]), "region"] = pd.Series(regions, index=df.index)

    if "mood_tags" not in df.columns:
        df["mood_tags"] = ""

    return df


def infer_mood_tags(row: pd.Series) -> str:
    """Derive mood tags from audio features."""
    tags = []

    valence = row.get("valence", 0.5)
    energy = row.get("energy", 0.5)
    danceability = row.get("danceability", 0.5)
    acousticness = row.get("acousticness", 0.5)
    instrumentalness = row.get("instrumentalness", 0.0)

    try:
        valence = float(valence) if pd.notna(valence) else 0.5
        energy = float(energy) if pd.notna(energy) else 0.5
        danceability = float(danceability) if pd.notna(danceability) else 0.5
        acousticness = float(acousticness) if pd.notna(acousticness) else 0.5
        instrumentalness = float(instrumentalness) if pd.notna(instrumentalness) else 0.0
    except (ValueError, TypeError):
        return ""

    mt = MOOD_THRESHOLDS

    if valence > mt["energetic_happy_valence"] and energy > mt["energetic_happy_energy"]:
        tags.extend(["energetic", "happy", "party"])
    elif valence > mt["energetic_happy_valence"]:
        tags.append("happy")
    elif energy > mt["energetic_happy_energy"]:
        tags.append("intense")

    if valence < mt["sad_valence"] and energy < mt["sad_energy"]:
        tags.extend(["sad", "melancholic"])
    elif valence < mt["sad_valence"]:
        tags.append("melancholic")

    if energy < mt["calm_energy"] and acousticness > mt["calm_acousticness"]:
        tags.extend(["calm", "peaceful"])
    elif energy < mt["calm_energy"]:
        tags.append("calm")

    if danceability > mt["danceable"]:
        tags.append("danceable")

    if acousticness > mt["acoustic"]:
        tags.append("acoustic")

    if (mt["romantic_valence_low"] < valence < mt["romantic_valence_high"]
            and mt["romantic_energy_low"] < energy < mt["romantic_energy_high"]
            and acousticness > mt["romantic_acousticness"]):
        tags.append("romantic")

    if instrumentalness > mt["instrumental"]:
        tags.append("instrumental")

    genre = str(row.get("genre", "")).lower()
    if genre in ("devotional", "classical", "sufi", "ghazal"):
        tags.append("devotional")

    if genre in ("bhojpuri", "haryanvi", "rajasthani", "punjabi", "gujarati"):
        if danceability > 0.65 and energy > 0.55:
            tags.extend(["energetic", "party", "danceable"])
        elif danceability > 0.65:
            tags.append("danceable")

    if (energy < mt["soothing_energy"] and acousticness > mt["soothing_acousticness"]
            and valence > mt["soothing_valence"]):
        tags.append("soothing")

    return ",".join(sorted(set(tags)))


def validate_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with missing name+artist, handle NaN features, fill empty strings."""
    before = len(df)
    df = df.copy()

    # Drop rows with empty name AND artist
    df = df.dropna(subset=["name", "artist"], how="all")
    df["name"] = df["name"].astype(str).str.strip()
    df["artist"] = df["artist"].astype(str).str.strip()
    df = df[
        (df["name"] != "") & (df["name"] != "nan") &
        (df["artist"] != "") & (df["artist"] != "nan")
    ]

    # Handle NaN in audio features — fill with column median
    for col in AUDIO_FEATURE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val).clip(0.0, 1.0)

    # Fill NaN strings
    str_cols = [
        "name", "artist", "language", "genre", "region", "mood_tags",
        "spotify_id", "preview", "img", "source", "release_date",
    ]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)
            # Clean "nan" strings
            df[col] = df[col].replace("nan", "")

    if "release_year" not in df.columns:
        for date_col in ("release_date", "date", "year"):
            if date_col in df.columns:
                df["release_year"] = df[date_col].map(parse_release_year)
                break
    else:
        df["release_year"] = df["release_year"].map(parse_release_year)

    if "popularity" in df.columns:
        df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce")
    if "chart_rank" in df.columns:
        df["chart_rank"] = pd.to_numeric(df["chart_rank"], errors="coerce")
    if "catalog_year" in df.columns:
        df["catalog_year"] = pd.to_numeric(df["catalog_year"], errors="coerce")

    df["india_affinity"] = build_india_affinity(
        df,
        artist_hints=INDIAN_ARTIST_HINTS,
        title_hints=INDIAN_TITLE_HINTS,
    )

    df.reset_index(drop=True, inplace=True)

    removed = before - len(df)
    if removed > 0:
        logger.info("Cleaned: removed %d invalid rows", removed)
    logger.info("Clean dataset: %d songs", len(df))

    return df


def build_enhanced_description(row: pd.Series) -> str:
    """Build a rich description including genre, language, and mood keywords.
    Example: 'Tum Hi Ho by Arijit Singh, bollywood, hindi. romantic, melancholic and dark, acoustic'
    """
    parts: list[str] = []

    name = str(row.get("name", "")).strip()
    artist = str(row.get("artist", "")).strip()
    if not name and not artist:
        return "unknown song"

    if name and artist:
        parts.append(f"{name} by {artist}")
    elif name:
        parts.append(name)
    elif artist:
        parts.append(artist)

    # Genre and language context
    meta_parts = []
    genre = str(row.get("genre", "")).strip()
    if genre and genre not in ("", "unknown", "pop"):
        meta_parts.append(genre.replace("_", " "))

    language = str(row.get("language", "")).strip()
    if language in LANGUAGE_DISPLAY_MAP:
        meta_parts.append(LANGUAGE_DISPLAY_MAP[language].lower())
    elif language and language != "en":
        meta_parts.append(language)

    if meta_parts:
        parts.append(", " + ", ".join(meta_parts))

    region = str(row.get("region", "")).strip().replace("_", " ")
    india_affinity = row.get("india_affinity", 0)
    try:
        india_affinity = float(india_affinity)
    except (TypeError, ValueError):
        india_affinity = 0
    if region and region not in ("western", "unknown") and india_affinity > 0:
        parts.append(f", {region}")

    release_year = parse_release_year(row.get("release_year") or row.get("release_date"))
    if release_year:
        parts.append(f", released {release_year}")

    try:
        catalog_year = int(float(row.get("catalog_year")))
    except (TypeError, ValueError):
        catalog_year = 0
    if catalog_year >= 2026:
        parts.append(", 2026 refreshed Indian catalog")

    # Audio feature descriptors (sorted by weight, highest first)
    descriptors: list[str] = []
    sorted_features = sorted(FEATURE_DESCRIPTORS, key=lambda x: x[5], reverse=True)
    for col, low_thresh, high_thresh, low_label, high_label, _weight in sorted_features:
        val = row.get(col)
        if val is None or pd.isna(val):
            continue
        try:
            val = float(val)
        except (ValueError, TypeError):
            continue
        if val <= low_thresh and low_label:
            descriptors.append(low_label)
        elif val >= high_thresh and high_label:
            descriptors.append(high_label)

    # Mood tags
    mood = str(row.get("mood_tags", "")).strip()
    if mood:
        mood_list = [m.strip() for m in mood.split(",") if m.strip()]
        existing = set(d.lower() for d in descriptors)
        for m in mood_list[:3]:
            if m.lower() not in existing:
                descriptors.append(m)

    if descriptors:
        parts.append(". " + ", ".join(descriptors))

    return "".join(parts) if parts else "unknown song"


def run_preprocessing(
    existing_csv: str = DATASET_PATH,
    output_path: Optional[str] = None,
) -> pd.DataFrame:
    """Run full preprocessing pipeline on the merged Music.csv."""

    # Load merged dataset
    if not Path(existing_csv).exists():
        logger.error("Dataset not found: %s", existing_csv)
        return pd.DataFrame()

    df = load_dataset(existing_csv)

    # Infer language/genre/region from source column
    df = infer_tags_from_source(df)

    # Infer mood tags for all rows
    mask = df["mood_tags"].astype(str).str.strip() == ""
    if mask.any():
        df.loc[mask, "mood_tags"] = df[mask].apply(infer_mood_tags, axis=1)
        logger.info("Inferred mood tags for %d songs", mask.sum())

    # Clean
    df = validate_and_clean(df)

    if df.empty:
        raise ValueError(
            f"Dataset at {existing_csv} produced 0 valid songs after cleaning. "
            "Regenerate Music.csv from the backup or re-run merge_datasets.py."
        )

    if output_path:
        df.to_csv(output_path, index=False)
        logger.info("Saved processed dataset to %s", output_path)

    # Stats
    logger.info("=== Dataset Statistics ===")
    logger.info("Total songs: %d", len(df))
    if "region" in df.columns:
        for region, count in df["region"].value_counts().items():
            logger.info("  %s: %d songs", region, count)
    if "language" in df.columns:
        for lang, count in df["language"].value_counts().head(10).items():
            logger.info("  Language '%s': %d songs", lang, count)
    if "source" in df.columns:
        for source, count in df["source"].value_counts().head(10).items():
            logger.info("  Source '%s': %d songs", source, count)

    # Preview stats
    has_preview = df["preview"].astype(str).str.startswith("http").sum()
    logger.info("  Songs with preview: %d / %d (%.1f%%)",
                 has_preview, len(df), 100 * has_preview / len(df) if len(df) > 0 else 0)

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PictoMusic Dataset Preprocessor")
    parser.add_argument("--dataset", default=DATASET_PATH, help="Path to Music.csv")
    parser.add_argument("--output", default=None, help="Output CSV path (optional)")
    args = parser.parse_args()

    run_preprocessing(
        existing_csv=args.dataset,
        output_path=args.output,
    )
