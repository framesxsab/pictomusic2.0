"""
PictoMusic UI Components
Reusable HTML rendering functions for the Streamlit interface.
"""

import urllib.parse

import pandas as pd
import streamlit as st

from security import escape_html


def render_hero_section(version_tag: str, subtitle: str) -> None:
    """Render the hero section with version badge, title, and subtitle."""
    st.markdown(
        f"""
        <div style="text-align: center; padding: 1rem 0 0.5rem;" class="hero-glow">
            <div class="version-badge">{escape_html(version_tag)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h1 class="hero-title">WHERE SIGHT<br>BECOMES SOUND</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="hero-subtitle">{escape_html(subtitle)}</p>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)


def render_stat_card(label: str, value: str, unit: str, color: str = "var(--primary)") -> None:
    """Render a single statistics card."""
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
) -> None:
    """Render a single song recommendation card."""
    safe_name = escape_html(song_name)
    safe_artist = escape_html(artist_name)

    tags_html = ""
    if genre or language:
        tag_items = []
        if genre and genre not in ("", "unknown", "pop"):
            tag_items.append(f'<span class="song-tag">{escape_html(genre)}</span>')
        if language and language not in ("", "en"):
            lang_map = {
                "hi": "Hindi", "ta": "Tamil", "te": "Telugu", "pa": "Punjabi",
                "bn": "Bengali", "kn": "Kannada", "ml": "Malayalam", "mr": "Marathi",
                "ur": "Urdu", "sa": "Sanskrit", "bh": "Bhojpuri", "as": "Assamese",
            }
            lang_display = lang_map.get(language, language)
            tag_items.append(f'<span class="song-tag">{escape_html(lang_display)}</span>')
        if tag_items:
            tags_html = f'<div class="song-meta">{"".join(tag_items)}</div>'

    st.markdown(
        f"""
        <div class="song-card">
            <div class="song-rank">Track #{idx + 1}</div>
            <div class="song-name">{safe_name}</div>
            <div class="song-artist">{safe_artist}</div>
            {tags_html}
            <div class="score-container">
                <div class="score-label">
                    <span class="score-text">Neural Match</span>
                    <span class="score-value">{score:.4f}</span>
                </div>
                <div class="score-bar-bg">
                    <div class="score-bar-fill" style="width: {score_pct:.1f}%;"></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_preview_or_fallback(
    song_name: str,
    artist_name: str,
    preview_url: str,
    spotify_id: str = "",
) -> None:
    """Render audio preview or fallback YouTube/Spotify search links."""
    if preview_url and str(preview_url).strip() and str(preview_url).strip().lower() != "no":
        st.audio(str(preview_url), format="audio/mp3")
    else:
        query = f"{song_name} {artist_name}".strip()
        encoded_query = urllib.parse.quote(query)

        yt_url = f"https://www.youtube.com/results?search_query={encoded_query}"

        if spotify_id and str(spotify_id).strip():
            sp_url = f"https://open.spotify.com/track/{spotify_id}"
        else:
            sp_url = f"https://open.spotify.com/search/{encoded_query}"

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
