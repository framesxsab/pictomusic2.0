"""Hybrid ranking for India-first visual music retrieval."""

from __future__ import annotations

import re
from datetime import date
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from config import (
    ARTWORK_WEIGHT,
    FRESHNESS_WEIGHT,
    INDIA_RELEVANCE_WEIGHT,
    INDIAN_GENRES,
    INDIAN_LANGUAGE_CODES,
    INDIAN_REGIONS,
    LANGUAGE_MATCH_WEIGHT,
    POPULARITY_WEIGHT,
    PREVIEW_IMPORTANCE_MARGIN,
    PREVIEW_TARGET_SHARE,
    PREVIEW_WEIGHT,
    RECENT_YEAR_THRESHOLD,
    REGION_MATCH_WEIGHT,
)


def _norm(value: object) -> str:
    return str(value or "").strip().lower()


def has_http(value: object) -> bool:
    return _norm(value).startswith("http")


def _clean_key_text(value: object) -> str:
    text = _norm(value)
    text = re.sub(r"\s*[\(\[]\s*from\s+.*?[\)\]]", " ", text)
    text = re.sub(r"\s+-\s+from\s+.*$", " ", text)
    text = re.sub(r"['\"`]", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _canonical_artist_key(value: object) -> str:
    parts = re.split(r"\s*(?:,|\||&|\band\b)\s*", _norm(value))
    cleaned = [_clean_key_text(part) for part in parts]
    return "|".join(sorted({part for part in cleaned if part})[:4])


def song_identity_key(row: pd.Series) -> str:
    """Return a stable song identity key for duplicate suppression."""
    title_key = _clean_key_text(row.get("name"))
    artist_key = _canonical_artist_key(row.get("artist"))
    if title_key:
        return f"{title_key}::{artist_key}"

    spotify_id = _clean_key_text(row.get("spotify_id"))
    if spotify_id:
        return f"spotify::{spotify_id}"
    return ""


def _score_column(df: pd.DataFrame) -> str:
    if "hybrid_score" in df.columns:
        return "hybrid_score"
    if "similarity_score" in df.columns:
        return "similarity_score"
    if "visual_score" in df.columns:
        return "visual_score"
    return ""


def _has_track_link(row: pd.Series) -> bool:
    if has_http(row.get("track_url")):
        return True
    spotify_id = str(row.get("spotify_id", "") or "").strip().lower()
    return bool(spotify_id and spotify_id != "nan")


def parse_release_year(value: object) -> Optional[int]:
    """Extract a plausible release year from mixed metadata values."""
    text = _norm(value)
    if not text or text in {"nan", "none", "no"}:
        return None

    match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    if not match:
        return None

    year = int(match.group(1))
    current_year = date.today().year + 1
    if 1900 <= year <= current_year:
        return year
    return None


def minmax_score(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if values.dropna().empty:
        return pd.Series(np.zeros(len(series)), index=series.index)

    min_value = values.min()
    max_value = values.max()
    if pd.isna(min_value) or pd.isna(max_value) or min_value == max_value:
        return pd.Series(np.zeros(len(series)), index=series.index)

    return ((values - min_value) / (max_value - min_value)).fillna(0.0).clip(0.0, 1.0)


def compute_india_affinity(row: pd.Series) -> float:
    """Score how likely a row is relevant to Indian listeners."""
    language = _norm(row.get("language"))
    genre = _norm(row.get("genre")).replace(" ", "_")
    region = _norm(row.get("region"))
    source = _norm(row.get("source"))

    score = 0.0
    if language in INDIAN_LANGUAGE_CODES:
        score += 0.45
    if genre in INDIAN_GENRES:
        score += 0.25
    if region in INDIAN_REGIONS:
        score += 0.25
    if source.startswith("regional_") or "bollywood" in source or "indian" in source:
        score += 0.20

    artist = _norm(row.get("artist"))
    title = _norm(row.get("name"))
    if any(hint in artist for hint in row.get("_artist_hints", ())):
        score += 0.12
    if any(re.search(rf"\b{re.escape(hint)}\b", title) for hint in row.get("_title_hints", ())):
        score += 0.08

    return min(score, 1.0)


def build_india_affinity(
    df: pd.DataFrame,
    artist_hints: Iterable[str],
    title_hints: Iterable[str],
) -> pd.Series:
    if df.empty:
        return pd.Series(dtype="float32")

    work = df.copy()
    work["_artist_hints"] = [artist_hints] * len(work)
    work["_title_hints"] = [title_hints] * len(work)
    return work.apply(compute_india_affinity, axis=1).astype("float32")


def apply_hybrid_ranking(
    results: pd.DataFrame,
    preferred_language: str = "any",
    preferred_region: str = "any",
    prefer_recent: bool = True,
    require_preview: bool = False,
    boost_indian: bool = False,
) -> pd.DataFrame:
    """Blend CLIP similarity with India, metadata, freshness, and media quality."""
    if results.empty:
        return results

    ranked = results.copy()
    base = pd.to_numeric(ranked.get("similarity_score", 0.0), errors="coerce").fillna(0.0)
    ranked["visual_score"] = base
    ranked["hybrid_score"] = base

    if boost_indian and "india_affinity" in ranked.columns:
        ranked["hybrid_score"] += ranked["india_affinity"].fillna(0.0) * INDIA_RELEVANCE_WEIGHT

    preferred_language = _norm(preferred_language)
    if preferred_language and preferred_language != "any" and "language" in ranked.columns:
        language_match = ranked["language"].map(_norm).eq(preferred_language).astype(float)
        ranked["hybrid_score"] += language_match * LANGUAGE_MATCH_WEIGHT

    preferred_region = _norm(preferred_region)
    if preferred_region and preferred_region != "any" and "region" in ranked.columns:
        region_match = ranked["region"].map(_norm).eq(preferred_region).astype(float)
        ranked["hybrid_score"] += region_match * REGION_MATCH_WEIGHT

    if prefer_recent:
        year_col = None
        for candidate in ("release_year", "year", "release_date", "date"):
            if candidate in ranked.columns:
                year_col = candidate
                break
        if year_col:
            years = ranked[year_col].map(parse_release_year)
            recent = years.fillna(0).ge(RECENT_YEAR_THRESHOLD).astype(float)
            ranked["hybrid_score"] += recent * FRESHNESS_WEIGHT
            ranked["release_year_inferred"] = years
        if "catalog_year" in ranked.columns:
            refreshed = pd.to_numeric(ranked["catalog_year"], errors="coerce").fillna(0).ge(2026).astype(float)
            ranked["hybrid_score"] += refreshed * (FRESHNESS_WEIGHT * 0.5)

    if "popularity" in ranked.columns:
        ranked["hybrid_score"] += minmax_score(ranked["popularity"]) * POPULARITY_WEIGHT
    elif "chart_rank" in ranked.columns:
        ranks = pd.to_numeric(ranked["chart_rank"], errors="coerce")
        max_rank = ranks.max()
        if not pd.isna(max_rank) and max_rank > 0:
            ranked["hybrid_score"] += ((max_rank - ranks + 1) / max_rank).fillna(0.0) * POPULARITY_WEIGHT

    if "preview" in ranked.columns:
        has_preview = ranked["preview"].map(has_http).astype(float)
        ranked["hybrid_score"] += has_preview * PREVIEW_WEIGHT
        if require_preview:
            ranked = ranked[has_preview.astype(bool)]

    if "img" in ranked.columns:
        ranked["hybrid_score"] += ranked["img"].map(has_http).astype(float) * ARTWORK_WEIGHT

    ranked.sort_values("hybrid_score", ascending=False, inplace=True)
    ranked.reset_index(drop=True, inplace=True)
    return ranked


def deduplicate_recommendations(results: pd.DataFrame) -> pd.DataFrame:
    """Collapse repeated song variants, keeping the most useful row for each song."""
    if results.empty or "name" not in results.columns:
        return results

    ranked = results.copy()
    score_col = _score_column(ranked)
    ranked["_original_rank"] = range(len(ranked))
    ranked["_song_key"] = ranked.apply(song_identity_key, axis=1)
    ranked["_has_preview"] = ranked.get("preview", "").map(has_http) if "preview" in ranked.columns else False
    ranked["_has_link"] = ranked.apply(_has_track_link, axis=1)
    ranked["_has_artwork"] = ranked.get("img", "").map(has_http) if "img" in ranked.columns else False

    sort_cols = ["_has_preview"]
    ascending = [False]
    if score_col:
        sort_cols.append(score_col)
        ascending.append(False)
    sort_cols.extend(["_has_link", "_has_artwork", "_original_rank"])
    ascending.extend([False, False, True])

    deduped = (
        ranked.sort_values(sort_cols, ascending=ascending)
        .drop_duplicates(subset=["_song_key"], keep="first")
    )

    if score_col:
        deduped.sort_values([score_col, "_original_rank"], ascending=[False, True], inplace=True)
    else:
        deduped.sort_values("_original_rank", inplace=True)

    return deduped.drop(
        columns=["_original_rank", "_song_key", "_has_preview", "_has_link", "_has_artwork"],
        errors="ignore",
    ).reset_index(drop=True)


def prioritize_preference_matches(
    results: pd.DataFrame,
    preferred_language: str = "any",
    preferred_region: str = "any",
) -> pd.DataFrame:
    """Keep explicit language/region selections ahead of generic visual matches."""
    if results.empty:
        return results

    preferred_language = _norm(preferred_language)
    preferred_region = _norm(preferred_region)
    has_language_pref = preferred_language and preferred_language != "any"
    has_region_pref = preferred_region and preferred_region != "any"
    if not has_language_pref and not has_region_pref:
        return results

    ranked = results.copy()
    match = pd.Series(True, index=ranked.index)
    if has_language_pref and "language" in ranked.columns:
        match &= ranked["language"].map(_norm).eq(preferred_language)
    if has_region_pref and "region" in ranked.columns:
        match &= ranked["region"].map(_norm).eq(preferred_region)

    if not bool(match.any()):
        return results

    return pd.concat([ranked[match], ranked[~match]], ignore_index=True)


def promote_preview_recommendations(
    results: pd.DataFrame,
    target_size: int,
    target_share: float = PREVIEW_TARGET_SHARE,
    importance_margin: float = PREVIEW_IMPORTANCE_MARGIN,
) -> pd.DataFrame:
    """Promote preview tracks into the visible set unless non-preview matches are much stronger."""
    if results.empty or target_size <= 0 or "preview" not in results.columns:
        return results

    score_col = _score_column(results)
    if not score_col:
        return results

    ranked = results.copy()
    ranked["_original_rank"] = range(len(ranked))
    ranked["_has_preview"] = ranked["preview"].map(has_http)

    visible_size = min(int(target_size), len(ranked))
    target_share = max(0.0, min(float(target_share), 1.0))
    available_previews = int(ranked["_has_preview"].sum())
    target_preview_count = min(available_previews, int(np.ceil(visible_size * target_share)))
    selected = list(ranked.index[:visible_size])

    def selected_preview_count() -> int:
        return int(ranked.loc[selected, "_has_preview"].sum())

    if selected_preview_count() >= target_preview_count:
        return ranked.drop(columns=["_original_rank", "_has_preview"]).reset_index(drop=True)

    outside_preview_indices = [
        idx for idx in ranked.index[visible_size:] if bool(ranked.at[idx, "_has_preview"])
    ]

    for candidate_idx in outside_preview_indices:
        selected_df = ranked.loc[selected]
        non_preview = selected_df[~selected_df["_has_preview"]]
        if non_preview.empty:
            break

        weakest_idx = non_preview.sort_values(
            [score_col, "_original_rank"], ascending=[True, False]
        ).index[0]
        score_gap = float(ranked.at[weakest_idx, score_col]) - float(ranked.at[candidate_idx, score_col])
        if score_gap > importance_margin:
            break

        selected[selected.index(weakest_idx)] = candidate_idx
        if selected_preview_count() >= target_preview_count:
            break

    selected_set = set(selected)
    selected_block = ranked.loc[selected].sort_values(
        [score_col, "_original_rank"], ascending=[False, True]
    )
    remainder = ranked.loc[[idx for idx in ranked.index if idx not in selected_set]]
    balanced = pd.concat([selected_block, remainder], ignore_index=True)
    return balanced.drop(columns=["_original_rank", "_has_preview"]).reset_index(drop=True)
