"""
PictoMusic Results Display
"""

import pandas as pd
import streamlit as st

from ranking import deduplicate_recommendations
from security import escape_html
from ui.components import (
    build_song_card_html,
    match_quality_label,
    render_preview_or_fallback,
    render_song_card,
    render_stat_card,
)


def mood_read_label(confidence: float) -> str:
    """Convert internal mood confidence into public-facing read strength."""
    value = max(0.0, min(float(confidence or 0.0), 1.0))
    if value >= 0.32:
        return "Clear visual read"
    if value >= 0.18:
        return "Balanced visual read"
    if value > 0:
        return "Exploratory visual read"
    return "Visual read ready"


def render_search_context(search_context: dict | None) -> None:
    """Render compact diagnostics for the retrieval profile used in the run."""
    if not search_context:
        return

    query = str(search_context.get("query", "") or "").strip()
    candidate_count = int(search_context.get("candidate_count", 0) or 0)
    mood_confidence = float(search_context.get("mood_confidence", 0.0) or 0.0)
    if not query and not candidate_count:
        return

    chips = "".join(
        [
            f'<span class="summary-chip">{candidate_count:,} songs considered</span>',
            f'<span class="summary-chip">{escape_html(mood_read_label(mood_confidence))}</span>',
        ]
    )
    st.markdown(
        "\n".join(
            [
                '<div class="search-context-panel">',
                '<div class="retrieval-summary-label">How this set was shaped</div>',
                f'<div class="search-context-query">{escape_html(query)}</div>',
                f'<div class="retrieval-summary-chips">{chips}</div>',
                '</div>',
            ]
        ),
        unsafe_allow_html=True,
    )


def render_results(
    recommendations: pd.DataFrame,
    search_context: dict | None = None,
) -> None:
    """Render the full results section with run context and song cards."""
    recommendations = deduplicate_recommendations(recommendations)

    st.markdown("<br>", unsafe_allow_html=True)

    render_search_context(search_context)

    # Stats row
    score_col = "hybrid_score" if "hybrid_score" in recommendations.columns else "similarity_score"
    if score_col in recommendations.columns:
        top_score = recommendations[score_col].max()
        avg_score = recommendations[score_col].mean()
        num_results = len(recommendations)
        avg_pct = min((avg_score / top_score) * 100, 100) if top_score > 0 else 0

        stat_cols = st.columns(3)
        with stat_cols[0]:
            render_stat_card("Best Fit", match_quality_label(100), "")
        with stat_cols[1]:
            render_stat_card("Set Quality", match_quality_label(avg_pct), "", "var(--accent-green)")
        with stat_cols[2]:
            render_stat_card("Tracks Found", str(num_results), "tracks", "var(--accent-amber)")

    st.markdown("<br>", unsafe_allow_html=True)

    # Render detected visual themes/moods if available
    detected_themes = st.session_state.get("detected_themes", [])
    if detected_themes:
        badges = "".join(
            f'<span class="detected-theme-chip">{escape_html(theme)}</span>'
            for theme in detected_themes
        )
        st.markdown(
            "\n".join(
                [
                    '<div class="detected-themes-panel">',
                    '<span class="detected-themes-label">Detected visual themes</span>',
                    f'<div class="detected-theme-list">{badges}</div>',
                    '</div>',
                ]
            ),
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="section-header">Curated <span class="section-accent">Set</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="section-subtitle">'
        "A tighter sequence shaped by mood, region, freshness, and listening variety.</p>",
        unsafe_allow_html=True,
    )

    # Determine available columns
    display_cols = ["name", "artist", "preview"]
    for score_candidate in ("similarity_score", "visual_score", "hybrid_score"):
        if score_candidate in recommendations.columns:
            display_cols.append(score_candidate)

    optional_cols = [
        "genre",
        "language",
        "region",
        "release_year",
        "release_year_inferred",
        "spotify_id",
        "intent_fit_score",
    ]
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

    cards_html = []
    for idx, row in recommendations.reset_index(drop=True).iterrows():
        song_name = str(row.get("name", "N/A"))
        artist_name = str(row.get("artist", "N/A"))
        score = row.get(score_col, 0)
        score_pct = min((score / max_score) * 100, 100) if max_score > 0 else 0

        genre = str(row.get("genre", "")) if "genre" in recommendations.columns else ""
        language = str(row.get("language", "")) if "language" in recommendations.columns else ""
        region = str(row.get("region", "")) if "region" in recommendations.columns else ""
        visual_score = row.get("visual_score") if "visual_score" in recommendations.columns else None
        intent_fit_score = (
            row.get("intent_fit_score")
            if "intent_fit_score" in recommendations.columns
            else None
        )
        release_year = ""
        for year_col in ("release_year", "release_year_inferred"):
            if year_col in recommendations.columns and str(row.get(year_col, "")).strip():
                release_year = str(row.get(year_col, "")).replace(".0", "")
                break

        img_url = str(row.get("img", "")) if "img" in recommendations.columns else ""
        preview = str(row.get("preview", "")) if "preview" in recommendations.columns else ""
        spotify_id = str(row.get("spotify_id", "")) if "spotify_id" in recommendations.columns else ""

        card_html = build_song_card_html(
            idx,
            song_name,
            artist_name,
            score,
            score_pct,
            genre=genre,
            language=language,
            region=region,
            visual_score=visual_score,
            intent_fit_score=intent_fit_score,
            release_year=release_year,
            img_url=img_url,
            preview_url=preview,
            spotify_id=spotify_id,
        )
        cards_html.append(card_html)

    st.markdown(
        f'<div class="soundtrack-scroll-container">{"".join(cards_html)}</div>'.replace("\n", ""),
        unsafe_allow_html=True,
    )
