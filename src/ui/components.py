"""
PictoMusic UI Components
Reusable HTML rendering functions for the Streamlit interface.
"""

import urllib.parse

from config import (
    HERO_TITLE,
    LANGUAGE_DISPLAY_MAP,
    SPOTIFY_SEARCH_URL,
    SPOTIFY_TRACK_URL,
    YOUTUBE_SEARCH_URL,
)
from security import escape_html


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


def render_stat_card(label: str, value: str, unit: str, color: str = "var(--primary)") -> None:
    """Render a single statistics card."""
    import streamlit as st

    st.markdown(
        f"""
        <div class="stat-card" style="border-left-color: {color};">
            <div class="stat-label">{escape_html(label)}</div>
            <div class="stat-value">{value}<span class="stat-unit" style="color:{color};">{escape_html(unit)}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
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
        art_html = '<div class="song-art-container"><span class="song-art-placeholder">🎵</span></div>'

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

    score_label = "Hybrid Match" if visual_score is not None else "Match"
    visual_html = ""
    if visual_score is not None:
        visual_html = f'<span class="visual-score">Visual {visual_score:.4f}</span>'

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
            f'<span class="score-value">{score:.4f}</span>',
            '</div>',
            visual_html,
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

        if spotify_id and str(spotify_id).strip():
            sp_url = f"{SPOTIFY_TRACK_URL}{spotify_id}"
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
