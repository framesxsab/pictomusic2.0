"""
PictoMusic UI Components
Reusable HTML rendering functions for the Streamlit interface.
"""

import urllib.parse
import re
from typing import Any

from config import (
    HERO_TITLE,
    LANGUAGE_DISPLAY_MAP,
    SPOTIFY_SEARCH_URL,
    SPOTIFY_TRACK_URL,
    YOUTUBE_SEARCH_URL,
)
from security import escape_html

SPOTIFY_TRACK_ID_RE = re.compile(r"^[A-Za-z0-9]{22}$")


def format_file_size(size_bytes: int) -> str:
    """Return a compact human-readable file size."""
    size = max(int(size_bytes or 0), 0)
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def match_quality_label(score_pct: float) -> str:
    """Convert an internal rank percentage to a user-facing quality label."""
    pct = max(0.0, min(float(score_pct or 0.0), 100.0))
    if pct >= 92:
        return "Excellent match"
    if pct >= 78:
        return "Strong match"
    if pct >= 62:
        return "Good match"
    return "Possible match"


def build_image_ready_html(
    source_label: str,
    detail: str,
    size_text: str,
    action_text: str = "Ready to analyze",
) -> str:
    """Build a compact accepted-image status panel."""
    return "\n".join(
        [
            '<div class="image-ready-panel">',
            '<div class="image-ready-kicker">Image locked</div>',
            f'<div class="image-ready-title">{escape_html(action_text)}</div>',
            '<div class="image-ready-meta">',
            f'<span>{escape_html(source_label)}</span>',
            f'<span>{escape_html(detail)}</span>',
            f'<span>{escape_html(size_text)}</span>',
            '</div>',
            '</div>',
        ]
    )


def render_image_ready_panel(
    source_label: str,
    detail: str,
    size_text: str,
    action_text: str = "Ready to analyze",
) -> None:
    """Render accepted-image status below the preview."""
    import streamlit as st

    st.markdown(
        build_image_ready_html(source_label, detail, size_text, action_text),
        unsafe_allow_html=True,
    )


def render_intake_panel_header(mode_label: str, hint: str) -> None:
    """Render the image intake section heading."""
    import streamlit as st

    st.markdown(
        f"""
        <div class="intake-shell">
            <div class="intake-eyebrow">Visual input</div>
            <div class="intake-title">{escape_html(mode_label)}</div>
            <div class="intake-hint">{escape_html(hint)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_analysis_stage(label: str, detail: str, progress: float) -> None:
    """Render a branded analysis stage with a deterministic progress bar."""
    import streamlit as st

    pct = max(0.0, min(float(progress), 1.0)) * 100
    st.markdown(
        f"""
        <div class="analysis-stage" role="status" aria-live="polite">
            <div class="analysis-loader">
                <div class="analysis-disc">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <div class="analysis-bars" aria-hidden="true">
                    <span></span><span></span><span></span><span></span><span></span>
                </div>
            </div>
            <div class="analysis-stage-copy">
                <div class="analysis-stage-label">{escape_html(label)}</div>
                <div class="analysis-stage-detail">{escape_html(detail)}</div>
            </div>
            <div class="analysis-stage-track">
                <div class="analysis-stage-fill" style="width: {pct:.0f}%;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_result_guidance(message: str, suggestions: list[str]) -> None:
    """Render directed empty-result recovery copy."""
    import streamlit as st

    items = "".join(f"<li>{escape_html(item)}</li>" for item in suggestions)
    st.markdown(
        f"""
        <div class="empty-guidance">
            <div class="empty-guidance-title">{escape_html(message)}</div>
            <ul>{items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def normalize_spotify_track_id(spotify_id: str) -> str:
    """Return a clean Spotify track id or empty string for invalid metadata."""
    value = str(spotify_id or "").strip()
    if value.lower() in {"", "nan", "none", "no"}:
        return ""
    if value.startswith("spotify:track:"):
        value = value.rsplit(":", 1)[-1]
    if "/track/" in value:
        value = value.split("/track/", 1)[1].split("?", 1)[0].split("/", 1)[0]
    return value if SPOTIFY_TRACK_ID_RE.fullmatch(value) else ""


def render_hero_section(version_tag: str, subtitle: str) -> None:
    """Render the hero section with version badge, title, and subtitle."""
    import streamlit as st

    st.markdown(
        f"""
        <div style="text-align: center; padding: 1rem 0 0.5rem;" class="hero-glow">
            <div class="version-badge">{escape_html(version_tag)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<h1 class="hero-title">{HERO_TITLE}</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="hero-subtitle">{escape_html(subtitle)}</p>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)


def build_retrieval_summary_html(
    preferences: dict[str, Any],
    image_detail: str,
) -> str:
    """Build a short pre-run summary of the current search settings."""
    language = str(preferences.get("language_label") or preferences.get("preferred_language") or "Any")
    region = str(preferences.get("region_label") or preferences.get("preferred_region") or "Any")
    preview_mode = "Preview-only" if preferences.get("require_preview") else "Preview-balanced"
    recency = "Freshness on" if preferences.get("prefer_recent") else "Freshness neutral"
    india = "India boost on" if preferences.get("boost_indian") else "Visual-first"
    top_k = str(preferences.get("top_k", "10"))

    chips = [language, region, preview_mode, recency, india, f"Top {top_k}"]
    chips_html = "".join(f'<span class="summary-chip">{escape_html(chip)}</span>' for chip in chips)
    return "\n".join(
        [
            '<div class="retrieval-summary">',
            '<div class="retrieval-summary-label">Run profile</div>',
            f'<div class="retrieval-summary-title">{escape_html(image_detail)}</div>',
            f'<div class="retrieval-summary-chips">{chips_html}</div>',
            '</div>',
        ]
    )


def render_retrieval_summary(preferences: dict[str, Any], image_detail: str) -> None:
    """Render the current search settings before analysis."""
    import streamlit as st

    st.markdown(
        build_retrieval_summary_html(preferences, image_detail),
        unsafe_allow_html=True,
    )


def render_stat_card(label: str, value: str, unit: str, color: str = "var(--primary)") -> None:
    """Render a single statistics card."""
    import streamlit as st

    st.markdown(
        build_stat_card_html(label, value, unit, color),
        unsafe_allow_html=True,
    )


def build_stat_card_html(label: str, value: str, unit: str, color: str = "var(--primary)") -> str:
    """Build stat card HTML with separated value and unit text."""
    safe_value = escape_html(str(value))
    safe_unit = escape_html(str(unit))
    unit_html = (
        f'<span class="stat-unit" style="color:{color};">{safe_unit}</span>'
        if safe_unit
        else ""
    )
    return "\n".join(
        line
        for line in [
            f'<div class="stat-card" style="--stat-accent: {color};">',
            f'<div class="stat-label">{escape_html(label)}</div>',
            '<div class="stat-value">',
            f'<span class="stat-number">{safe_value}</span>',
            unit_html,
            '</div>',
            '</div>',
        ]
        if line
    )


def render_song_card(
    idx: int,
    song_name: str,
    artist_name: str,
    score: float,
    score_pct: float,
    genre: str = "",
    language: str = "",
    region: str = "",
    visual_score: float | None = None,
    intent_fit_score: float | None = None,
    release_year: str = "",
    img_url: str = "",
) -> None:
    """Render a single song recommendation card."""
    import streamlit as st

    st.markdown(
        build_song_card_html(
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
        ),
        unsafe_allow_html=True,
    )


def build_song_card_html(
    idx: int,
    song_name: str,
    artist_name: str,
    score: float,
    score_pct: float,
    genre: str = "",
    language: str = "",
    region: str = "",
    visual_score: float | None = None,
    intent_fit_score: float | None = None,
    release_year: str = "",
    img_url: str = "",
) -> str:
    """Build card HTML without leading indentation that Markdown can treat as code."""
    safe_name = escape_html(song_name)
    safe_artist = escape_html(artist_name)
    safe_img_url = escape_html(img_url) if img_url and img_url.startswith("http") else ""

    if safe_img_url:
        art_html = f'<div class="song-art-container"><img class="song-art" src="{safe_img_url}" alt="{safe_name} cover"></div>'
    else:
        art_html = '<div class="song-art-container"><span class="song-art-placeholder" aria-hidden="true">&#9835;</span></div>'

    tags_html = ""
    if genre or language or region or release_year:
        tag_items = []
        if genre and genre not in ("", "unknown", "pop"):
            tag_items.append(f'<span class="song-tag">{escape_html(genre)}</span>')
        if language and language not in ("", "en"):
            lang_display = LANGUAGE_DISPLAY_MAP.get(language, language)
            tag_items.append(f'<span class="song-tag">{escape_html(lang_display)}</span>')
        if region and region not in ("", "western", "unknown"):
            tag_items.append(f'<span class="song-tag">{escape_html(region.replace("_", " "))}</span>')
        if release_year and release_year not in ("", "nan", "none"):
            tag_items.append(f'<span class="song-tag">{escape_html(str(release_year))}</span>')
        if tag_items:
            tags_html = f'<div class="song-meta">{"".join(tag_items)}</div>'

    score_label = "Match confidence"
    quality_label = match_quality_label(score_pct)
    visual_html = ""
    if visual_score is not None:
        visual_html = '<span class="match-reason">Visual fit</span>'
    intent_html = ""
    if intent_fit_score is not None and float(intent_fit_score) > 0.04:
        intent_html = '<span class="match-reason">Mood aligned</span>'

    return "\n".join(
        line
        for line in [
            '<div class="song-card">',
            art_html,
            '<div class="song-details">',
            f'<div class="song-rank">Track #{idx + 1}</div>',
            f'<div class="song-name">{safe_name}</div>',
            f'<div class="song-artist">{safe_artist}</div>',
            tags_html,
            '<div class="score-container">',
            '<div class="score-label">',
            f'<span class="score-text">{score_label}</span>',
            f'<span class="score-value">{quality_label}</span>',
            '</div>',
            f'<div class="match-reasons">{visual_html}{intent_html}</div>' if visual_html or intent_html else "",
            '<div class="score-bar-bg">',
            f'<div class="score-bar-fill" style="width: {score_pct:.1f}%;"></div>',
            '</div>',
            '</div>',
            '</div>',
            '</div>',
        ]
        if line
    )


def render_preview_or_fallback(
    song_name: str,
    artist_name: str,
    preview_url: str,
    spotify_id: str = "",
) -> None:
    """Render audio preview or fallback YouTube/Spotify search links."""
    import streamlit as st

    if preview_url and str(preview_url).strip() and str(preview_url).strip().lower() != "no":
        st.audio(str(preview_url), format="audio/mp3")
    else:
        query = f"{song_name} {artist_name}".strip()
        encoded_query = urllib.parse.quote(query)

        yt_url = f"{YOUTUBE_SEARCH_URL}{encoded_query}"

        track_id = normalize_spotify_track_id(spotify_id)
        if track_id:
            sp_url = f"{SPOTIFY_TRACK_URL}{track_id}"
        else:
            sp_url = f"{SPOTIFY_SEARCH_URL}{encoded_query}"

        st.markdown(
            f"""
            <div class="no-preview">
                <span>Preview unavailable</span>
                <a href="{yt_url}" target="_blank" rel="noopener noreferrer"
                   style="color: #ff0000;">&#9654; YouTube</a>
                <a href="{sp_url}" target="_blank" rel="noopener noreferrer"
                   style="color: #1DB954;">&#9835; Spotify</a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
