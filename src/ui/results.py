"""
PictoMusic Results Display
"""

import pandas as pd
import streamlit as st

from security import escape_html
from ui.components import render_preview_or_fallback, render_song_card, render_stat_card


def render_results(recommendations: pd.DataFrame) -> None:
    """Render the full results section including stats and song cards."""
    st.markdown("<br>", unsafe_allow_html=True)

    # Stats row
    if "similarity_score" in recommendations.columns:
        top_score = recommendations["similarity_score"].max()
        avg_score = recommendations["similarity_score"].mean()
        num_results = len(recommendations)

        stat_cols = st.columns(3)
        with stat_cols[0]:
            render_stat_card("Top Match", f"{top_score:.3f}", "SIM")
        with stat_cols[1]:
            render_stat_card("Avg Score", f"{avg_score:.3f}", "AVG", "#d400ff")
        with stat_cols[2]:
            render_stat_card("Tracks Found", str(num_results), "TRACKS", "#00d4ff")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header">\U0001f3b5 Neural <span class="section-accent">Recommendations</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1.5rem;">'
        "Tracks ranked by visual-audio resonance</p>",
        unsafe_allow_html=True,
    )

    # Determine available columns
    display_cols = ["name", "artist", "preview"]
    if "similarity_score" in recommendations.columns:
        display_cols.append("similarity_score")

    optional_cols = ["genre", "language", "spotify_id"]
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
        recommendations["similarity_score"].max()
        if "similarity_score" in recommendations.columns
        else 1.0
    )

    for idx, row in recommendations.reset_index(drop=True).iterrows():
        song_name = str(row.get("name", "N/A"))
        artist_name = str(row.get("artist", "N/A"))
        score = row.get("similarity_score", 0)
        score_pct = min((score / max_score) * 100, 100) if max_score > 0 else 0

        genre = str(row.get("genre", "")) if "genre" in recommendations.columns else ""
        language = str(row.get("language", "")) if "language" in recommendations.columns else ""

        render_song_card(idx, song_name, artist_name, score, score_pct, genre, language)

        preview = str(row.get("preview", "")) if "preview" in recommendations.columns else ""
        spotify_id = str(row.get("spotify_id", "")) if "spotify_id" in recommendations.columns else ""
        render_preview_or_fallback(song_name, artist_name, preview, spotify_id)
