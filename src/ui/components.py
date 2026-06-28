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
MISSING_PREVIEW_VALUES = {"", "no", "nan", "none", "null"}


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
        '<div class="intake-shell">'
        '<div class="intake-eyebrow">Visual input</div>'
        f'<div class="intake-title">{escape_html(mode_label)}</div>'
        f'<div class="intake-hint">{escape_html(hint)}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_analysis_stage(label: str, detail: str, progress: float) -> None:
    """Render a branded analysis stage with a deterministic progress bar."""
    import streamlit as st

    pct = max(0.0, min(float(progress), 1.0)) * 100
    st.markdown(
        '<div class="analysis-stage" role="status" aria-live="polite">'
        '<div class="analysis-loader">'
        '<div class="analysis-disc"><span></span><span></span><span></span></div>'
        '<div class="analysis-bars" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>'
        '</div>'
        '<div class="analysis-stage-copy">'
        f'<div class="analysis-stage-label">{escape_html(label)}</div>'
        f'<div class="analysis-stage-detail">{escape_html(detail)}</div>'
        '</div>'
        '<div class="analysis-stage-track">'
        f'<div class="analysis-stage-fill" style="width: {pct:.0f}%;"></div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_empty_result_guidance(message: str, suggestions: list[str]) -> None:
    """Render directed empty-result recovery copy."""
    import streamlit as st

    items = "".join(f"<li>{escape_html(item)}</li>" for item in suggestions)
    st.markdown(
        '<div class="empty-guidance">'
        f'<div class="empty-guidance-title">{escape_html(message)}</div>'
        f'<ul>{items}</ul>'
        '</div>',
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


def has_playable_preview_url(preview_url: str) -> bool:
    """Return True only for remote preview URLs that should render as audio."""
    value = str(preview_url or "").strip()
    if value.lower() in MISSING_PREVIEW_VALUES:
        return False

    parsed = urllib.parse.urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def render_hero_section(version_tag: str, subtitle: str) -> None:
    """Render the studio-console hero section."""
    import streamlit as st

    st.markdown(
        '<section class="studio-hero">'
        '<div class="hero-topline">'
        f'<div class="version-badge">{escape_html(version_tag)}</div>'
        '<div class="hero-status">Ready for analysis</div>'
        '</div>'
        '<div class="hero-grid">'
        '<div class="hero-copy">'
        f'<h1 class="hero-title">{HERO_TITLE}</h1>'
        f'<p class="hero-subtitle">{escape_html(subtitle)}</p>'
        '</div>'
        '<div class="hero-console" aria-hidden="true">'
        '<div class="console-card console-card-primary">'
        '<div class="console-kicker">Image read</div>'
        '<div class="console-title">Mood palette</div>'
        '<div class="console-wave">'
        '<span></span><span></span><span></span><span></span><span></span>'
        '<span></span><span></span><span></span><span></span><span></span>'
        '</div>'
        '</div>'
        '<div class="console-card">'
        '<div class="console-kicker">Context</div>'
        '<div class="console-title">India-aware</div>'
        '</div>'
        '<div class="console-card">'
        '<div class="console-kicker">Playback</div>'
        '<div class="console-title">Preview-ready</div>'
        '</div>'
        '</div>'
        '</div>'
        '<div class="hero-meter" aria-hidden="true">'
        '<span></span><span></span><span></span><span></span><span></span>'
        '<span></span><span></span><span></span><span></span><span></span>'
        '<span></span><span></span><span></span><span></span><span></span>'
        '</div>'
        '</section>',
        unsafe_allow_html=True,
    )


def render_workspace_section_header(eyebrow: str, title: str, detail: str) -> None:
    """Render a consistent section header for the two main work areas."""
    import streamlit as st

    st.markdown(
        '<div class="workspace-header">'
        f'<div class="workspace-eyebrow">{escape_html(eyebrow)}</div>'
        f'<div class="workspace-title">{escape_html(title)}</div>'
        f'<div class="workspace-detail">{escape_html(detail)}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def build_retrieval_summary_html(
    preferences: dict[str, Any],
    image_detail: str,
) -> str:
    """Build a short pre-run summary of the current search settings."""
    language = str(preferences.get("language_label") or preferences.get("preferred_language") or "Any")
    region = str(preferences.get("region_label") or preferences.get("preferred_region") or "Any")
    preview_mode = "Playable previews" if preferences.get("require_preview") else "Preview balanced"
    recency = "Fresh releases" if preferences.get("prefer_recent") else "All eras"
    india = "India-first" if preferences.get("boost_indian") else "Visual-first"
    top_k = str(preferences.get("top_k", "10"))

    chips = [language, region, preview_mode, recency, india, f"Top {top_k}"]
    chips_html = "".join(f'<span class="summary-chip">{escape_html(chip)}</span>' for chip in chips)
    return "\n".join(
        [
            '<div class="retrieval-summary">',
            '<div class="retrieval-summary-label">Session profile</div>',
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
    preview_url: str = "",
    spotify_id: str = "",
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
            preview_url=preview_url,
            spotify_id=spotify_id,
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
    preview_url: str = "",
    spotify_id: str = "",
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
        seen = set()

        def add_tag(val: str, clean_fn=lambda x: x):
            if not val:
                return
            val_clean = str(val).strip()
            val_lower = val_clean.lower()
            if val_lower and val_lower not in seen and val_lower not in ("unknown", "pop", "en", "western"):
                seen.add(val_lower)
                tag_items.append(f'<span class="song-tag">{escape_html(clean_fn(val_clean))}</span>')

        add_tag(genre)
        if language:
            lang_display = LANGUAGE_DISPLAY_MAP.get(language, language)
            add_tag(lang_display)
        if region:
            add_tag(region, clean_fn=lambda x: x.replace("_", " "))
        if release_year:
            add_tag(str(release_year))

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

    # Embedded player or search links
    player_html = ""
    preview_url_str = str(preview_url or "").strip()
    if has_playable_preview_url(preview_url_str):
        player_html = f'<div class="song-player-container"><audio src="{escape_html(preview_url_str)}" controls></audio></div>'
    else:
        query = f"{song_name} {artist_name}".strip()
        encoded_query = urllib.parse.quote(query)
        yt_url = f"{YOUTUBE_SEARCH_URL}{encoded_query}"

        track_id = normalize_spotify_track_id(spotify_id)
        if track_id:
            sp_url = f"{SPOTIFY_TRACK_URL}{track_id}"
        else:
            sp_url = f"{SPOTIFY_SEARCH_URL}{encoded_query}"

        player_html = (
            '<div class="song-player-container">'
            '<div class="no-preview">'
            '<span>Preview unavailable</span>'
            f'<a href="{escape_html(yt_url)}" target="_blank" rel="noopener noreferrer" style="color: #ff0000; text-decoration: none;">&#9654; YouTube</a>'
            f'<a href="{escape_html(sp_url)}" target="_blank" rel="noopener noreferrer" style="color: #1DB954; text-decoration: none;">&#9835; Spotify</a>'
            '</div>'
            '</div>'
        )

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
            player_html,
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

    preview_url_str = str(preview_url or "").strip()
    if has_playable_preview_url(preview_url_str):
        st.audio(preview_url_str, format="audio/mp3")
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
            '<div class="no-preview">'
            '<span>Preview unavailable</span>'
            f'<a href="{yt_url}" target="_blank" rel="noopener noreferrer" style="color: #ff0000;">&#9654; YouTube</a>'
            f'<a href="{sp_url}" target="_blank" rel="noopener noreferrer" style="color: #1DB954;">&#9835; Spotify</a>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)


def build_dashboard_welcome_html() -> str:
    """Build the empty-state console shown before analysis."""
    return (
        '<div class="welcome-deck">'
        '<div class="deck-vinyl-wrapper" aria-hidden="true">'
        '<div class="deck-vinyl">'
        '<div class="vinyl-groove-1"></div>'
        '<div class="vinyl-groove-2"></div>'
        '<div class="vinyl-label"><div class="vinyl-label-center"></div></div>'
        '</div>'
        '</div>'
        '<div class="deck-msg">'
        '<h3 class="deck-title">Ready for a visual</h3>'
        '<p class="deck-desc">Upload a frame or paste a picture URL to prepare the listening profile.</p>'
        '</div>'
        '</div>'
    )


def render_dashboard_welcome() -> None:
    """Render an ambient welcome console when no image has been analyzed yet."""
    import streamlit as st

    st.markdown(
        build_dashboard_welcome_html(),
        unsafe_allow_html=True,
    )
