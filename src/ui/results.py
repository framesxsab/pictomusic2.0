"""
PictoMusic Results Display
"""

import pandas as pd
import streamlit as st

from ranking import deduplicate_recommendations
from security import escape_html
from ui.components import render_preview_or_fallback, render_song_card, render_stat_card


def render_catalog_health(stats: dict) -> None:
    """Render catalog health stats after a successful recommendation."""
    if not stats:
        return

    stat_cols = st.columns(4)
    with stat_cols[0]:
        render_stat_card("Catalog", f"{stats.get('songs', 0):,}", "songs")
    with stat_cols[1]:
        render_stat_card("India Signals", f"{stats.get('india_pct', 0):.0f}", "%", "var(--accent-green)")
    with stat_cols[2]:
        render_stat_card("Previews", f"{stats.get('preview_pct', 0):.0f}", "%", "var(--accent-warm)")
    with stat_cols[3]:
        render_stat_card("Languages", str(stats.get("languages", 0)), "langs", "var(--accent-rose)")


def render_results(recommendations: pd.DataFrame, catalog_stats: dict | None = None) -> None:
    """Render the full results section including stats and song cards."""
    recommendations = deduplicate_recommendations(recommendations)

    st.markdown("<br>", unsafe_allow_html=True)

    render_catalog_health(catalog_stats or {})
    st.markdown("<br>", unsafe_allow_html=True)

    # Stats row
    score_col = "hybrid_score" if "hybrid_score" in recommendations.columns else "similarity_score"
    if score_col in recommendations.columns:
        top_score = recommendations[score_col].max()
        avg_score = recommendations[score_col].mean()
        num_results = len(recommendations)

        stat_cols = st.columns(3)
        with stat_cols[0]:
            render_stat_card("Top Match", f"{top_score:.3f}", "score")
        with stat_cols[1]:
            render_stat_card("Avg Score", f"{avg_score:.3f}", "avg", "var(--accent-green)")
        with stat_cols[2]:
            render_stat_card("Tracks Found", str(num_results), "tracks", "var(--accent-warm)")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header">Music <span class="section-accent">Recommendations</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1.5rem;">'
        "Tracks ranked by visual match, Indian relevance, currentness, and playable metadata</p>",
        unsafe_allow_html=True,
    )

    # Determine available columns
    display_cols = ["name", "artist", "preview"]
    for score_candidate in ("similarity_score", "visual_score", "hybrid_score"):
        if score_candidate in recommendations.columns:
            display_cols.append(score_candidate)

    optional_cols = ["genre", "language", "region", "release_year", "release_year_inferred", "spotify_id"]
    for col in optional_cols:
        if col in recommendations.columns:
            display_cols.append(col)

    missing_cols = [
        c for c in ["name", "artist"]
        if c not in recommendations.columns
    ]
    if missing_cols:
        st.error(f"Missing columns: {', '.join(missing_cols)}. Check dataset.")
        return

    max_score = (
        recommendations[score_col].max()
        if score_col in recommendations.columns
        else 1.0
    )

    for idx, row in recommendations.reset_index(drop=True).iterrows():
        song_name = str(row.get("name", "N/A"))
        artist_name = str(row.get("artist", "N/A"))
        score = row.get(score_col, 0)
        score_pct = min((score / max_score) * 100, 100) if max_score > 0 else 0

        genre = str(row.get("genre", "")) if "genre" in recommendations.columns else ""
        language = str(row.get("language", "")) if "language" in recommendations.columns else ""
        region = str(row.get("region", "")) if "region" in recommendations.columns else ""
        visual_score = row.get("visual_score") if "visual_score" in recommendations.columns else None
        release_year = ""
        for year_col in ("release_year", "release_year_inferred"):
            if year_col in recommendations.columns and str(row.get(year_col, "")).strip():
                release_year = str(row.get(year_col, "")).replace(".0", "")
                break

        img_url = str(row.get("img", "")) if "img" in recommendations.columns else ""

        render_song_card(
            idx,
            song_name,
            artist_name,
            score,
            score_pct,
            genre,
            language,
            region,
            visual_score,
            release_year,
            img_url,
        )

        preview = str(row.get("preview", "")) if "preview" in recommendations.columns else ""
        spotify_id = str(row.get("spotify_id", "")) if "spotify_id" in recommendations.columns else ""
        render_preview_or_fallback(song_name, artist_name, preview, spotify_id)
