"""
PictoMusic Results Display
"""

import pandas as pd
import streamlit as st

from ranking import deduplicate_recommendations
from security import escape_html
from ui.components import (
    match_quality_label,
    render_preview_or_fallback,
    render_song_card,
    render_stat_card,
)


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


def render_search_context(search_context: dict | None) -> None:
    """Render compact diagnostics for the retrieval profile used in the run."""
    if not search_context:
        return

    query = str(search_context.get("query", "") or "").strip()
    candidate_count = int(search_context.get("candidate_count", 0) or 0)
    mood_confidence = float(search_context.get("mood_confidence", 0.0) or 0.0)
    if not query and not candidate_count:
        return

    st.markdown(
        f"""
        <div style="background: rgba(255, 249, 235, 0.02); border: 1px solid var(--glass-border);
                    border-radius: 0.75rem; padding: 0.85rem 1rem; margin-bottom: 1rem;">
            <div style="font-size: 0.65rem; font-weight: 800; color: var(--text-muted);
                        text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.35rem;">
                Retrieval Profile
            </div>
            <div style="color: var(--text-secondary); font-size: 0.82rem; line-height: 1.5;">
                {escape_html(query)}
            </div>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.65rem;">
                <span class="song-tag">{candidate_count:,} candidates</span>
                <span class="song-tag">confidence {mood_confidence:.3f}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_results(
    recommendations: pd.DataFrame,
    catalog_stats: dict | None = None,
    search_context: dict | None = None,
) -> None:
    """Render the full results section including stats and song cards."""
    recommendations = deduplicate_recommendations(recommendations)

    st.markdown("<br>", unsafe_allow_html=True)

    render_catalog_health(catalog_stats or {})
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
            render_stat_card("Tracks Found", str(num_results), "tracks", "var(--accent-warm)")

    st.markdown("<br>", unsafe_allow_html=True)

    # Render detected visual themes/moods if available
    detected_themes = st.session_state.get("detected_themes", [])
    if detected_themes:
        badges = "".join(
            f'<span style="display: inline-block; background: var(--primary-dim); border: 1px solid var(--border-glow); '
            f'color: var(--accent-warm); font-size: 0.72rem; font-weight: 700; border-radius: 9999px; '
            f'padding: 0.3rem 0.75rem; margin-right: 0.4rem; margin-bottom: 0.4rem; text-transform: uppercase; '
            f'letter-spacing: 0.05em;">'
            f'{escape_html(theme)}</span>'
            for theme in detected_themes
        )
        st.markdown(
            f"""
            <div style="background: rgba(255, 249, 235, 0.02); border: 1px solid var(--glass-border);
                        border-radius: 0.75rem; padding: 0.85rem 1rem; margin-bottom: 1.5rem; display: flex;
                        align-items: center; gap: 0.75rem; flex-wrap: wrap;">
                <span style="font-size: 0.65rem; font-weight: 800; color: var(--text-muted);
                            text-transform: uppercase; letter-spacing: 0.1em; flex-shrink: 0;">
                    Detected Visual Themes
                </span>
                <div style="display: flex; flex-wrap: wrap; align-items: center;">
                    {badges}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="section-header">Music <span class="section-accent">Recommendations</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1.5rem;">'
        "Tracks arranged by visual feel, mood, freshness, and listening variety</p>",
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
            intent_fit_score,
            release_year,
            img_url,
        )

        preview = str(row.get("preview", "")) if "preview" in recommendations.columns else ""
        spotify_id = str(row.get("spotify_id", "")) if "spotify_id" in recommendations.columns else ""
        render_preview_or_fallback(song_name, artist_name, preview, spotify_id)
