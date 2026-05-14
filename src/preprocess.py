"""
PictoMusic Preprocessing Pipeline
Dataset loading, tagging, cleaning, and enhanced description building.
Handles the merged Music.csv (91K+ songs with source column from multiple Indian datasets).
"""

import argparse
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from config import (
    AUDIO_FEATURE_COLUMNS,
    DATASET_PATH,
    FEATURE_DESCRIPTORS,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Mapping from source column values to (language, genre, region)
SOURCE_TAG_MAP = {
    "original":            ("en", "pop",       "western"),
    "spotify_tracks":      ("hi", "bollywood", "bollywood"),
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


def load_dataset(path: str) -> pd.DataFrame:
    """Load the merged Music.csv dataset."""
    df = pd.read_csv(path)
    logging.info("Loaded dataset: %d songs from %s", len(df), path)
    return df


def infer_tags_from_source(df: pd.DataFrame) -> pd.DataFrame:
    """Add language, genre, and region columns based on the source column."""
    df = df.copy()

    if "source" not in df.columns:
        df["language"] = "en"
        df["genre"] = "pop"
        df["region"] = "western"
        df["mood_tags"] = ""
        return df

    languages = []
    genres = []
    regions = []

    for source in df["source"]:
        source_str = str(source).strip()
        lang, genre, region = SOURCE_TAG_MAP.get(source_str, ("en", "pop", "western"))
        languages.append(lang)
        genres.append(genre)
        regions.append(region)

    df["language"] = languages
    df["genre"] = genres
    df["region"] = regions

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

    if valence > 0.65 and energy > 0.65:
        tags.extend(["energetic", "happy", "party"])
    elif valence > 0.65:
        tags.append("happy")
    elif energy > 0.65:
        tags.append("intense")

    if valence < 0.3 and energy < 0.4:
        tags.extend(["sad", "melancholic"])
    elif valence < 0.3:
        tags.append("melancholic")

    if energy < 0.35 and acousticness > 0.6:
        tags.extend(["calm", "peaceful"])
    elif energy < 0.35:
        tags.append("calm")

    if danceability > 0.7:
        tags.append("danceable")

    if acousticness > 0.7:
        tags.append("acoustic")

    if 0.35 < valence < 0.65 and 0.35 < energy < 0.65 and acousticness > 0.4:
        tags.append("romantic")

    if instrumentalness > 0.5:
        tags.append("instrumental")

    genre = str(row.get("genre", "")).lower()
    if genre in ("devotional", "classical", "sufi", "ghazal"):
        tags.append("devotional")

    if energy < 0.45 and acousticness > 0.5 and valence > 0.3:
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
    str_cols = ["name", "artist", "language", "genre", "region", "mood_tags",
                "spotify_id", "preview", "img"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)
            # Clean "nan" strings
            df[col] = df[col].replace("nan", "")

    df.reset_index(drop=True, inplace=True)

    removed = before - len(df)
    if removed > 0:
        logging.info("Cleaned: removed %d invalid rows", removed)
    logging.info("Clean dataset: %d songs", len(df))

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
    lang_map = {
        "hi": "hindi", "ta": "tamil", "te": "telugu",
        "pa": "punjabi", "bn": "bengali", "kn": "kannada", "ml": "malayalam",
        "mr": "marathi", "ur": "urdu", "sa": "sanskrit", "bh": "bhojpuri",
        "as": "assamese", "gu": "gujarati", "or": "odia",
    }
    if language in lang_map:
        meta_parts.append(lang_map[language])
    elif language and language != "en":
        meta_parts.append(language)

    if meta_parts:
        parts.append(", " + ", ".join(meta_parts))

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
        logging.error("Dataset not found: %s", existing_csv)
        return pd.DataFrame()

    df = load_dataset(existing_csv)

    # Infer language/genre/region from source column
    df = infer_tags_from_source(df)

    # Infer mood tags for all rows
    mask = df["mood_tags"].astype(str).str.strip() == ""
    if mask.any():
        df.loc[mask, "mood_tags"] = df[mask].apply(infer_mood_tags, axis=1)
        logging.info("Inferred mood tags for %d songs", mask.sum())

    # Clean
    df = validate_and_clean(df)

    if output_path:
        df.to_csv(output_path, index=False)
        logging.info("Saved processed dataset to %s", output_path)

    # Stats
    logging.info("=== Dataset Statistics ===")
    logging.info("Total songs: %d", len(df))
    if "region" in df.columns:
        for region, count in df["region"].value_counts().items():
            logging.info("  %s: %d songs", region, count)
    if "language" in df.columns:
        for lang, count in df["language"].value_counts().head(10).items():
            logging.info("  Language '%s': %d songs", lang, count)
    if "source" in df.columns:
        for source, count in df["source"].value_counts().head(10).items():
            logging.info("  Source '%s': %d songs", source, count)

    # Preview stats
    has_preview = df["preview"].astype(str).str.startswith("http").sum()
    logging.info("  Songs with preview: %d / %d (%.1f%%)",
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
