"""Tests for UI HTML builders."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ui.components import (
    build_dashboard_welcome_html,
    build_image_ready_html,
    build_retrieval_summary_html,
    build_song_card_html,
    build_stat_card_html,
    format_file_size,
    has_playable_preview_url,
    match_quality_label,
    normalize_spotify_track_id,
)


def test_song_card_without_tags_does_not_indent_score_as_markdown_code():
    html = build_song_card_html(
        idx=0,
        song_name="Juke Jam (feat. Justin Bieber & Towkio)",
        artist_name="Chance the Rapper",
        score=0.554,
        score_pct=80.0,
        visual_score=0.459,
        intent_fit_score=0.22,
    )

    assert '<div class="score-container">' in html
    assert "\n    <div class=\"score-container\">" not in html
    assert "&amp;" in html
    assert "Strong match" in html
    assert "Visual fit" in html
    assert "Mood aligned" in html
    assert "0.5540" not in html
    assert "Visual 0." not in html
    assert "Intent +" not in html


def test_song_card_escapes_user_visible_text():
    html = build_song_card_html(
        idx=0,
        song_name="<script>alert(1)</script>",
        artist_name="A & B",
        score=0.5,
        score_pct=50.0,
    )

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "A &amp; B" in html


def test_song_card_renders_artwork_when_provided():
    html = build_song_card_html(
        idx=0,
        song_name="Song Name",
        artist_name="Artist Name",
        score=0.8,
        score_pct=80.0,
        img_url="https://i.scdn.co/image/test",
    )
    assert '<img class="song-art" src="https://i.scdn.co/image/test"' in html


def test_song_card_renders_placeholder_when_no_image_provided():
    html = build_song_card_html(
        idx=0,
        song_name="Song Name",
        artist_name="Artist Name",
        score=0.8,
        score_pct=80.0,
        img_url="",
    )
    assert 'song-art-placeholder' in html
    assert "&#9835;" in html
    assert "ð" not in html

def test_song_card_falls_back_for_invalid_preview_metadata():
    for preview_value in ["nan", "none", "no", "javascript:alert(1)", "/preview.mp3"]:
        html = build_song_card_html(
            idx=0,
            song_name="Song Name",
            artist_name="Artist Name",
            score=0.8,
            score_pct=80.0,
            preview_url=preview_value,
        )

        assert "<audio" not in html
        assert "Preview unavailable" in html
        assert "YouTube" in html
        assert "Spotify" in html


def test_song_card_embeds_only_remote_preview_urls():
    html = build_song_card_html(
        idx=0,
        song_name="Song Name",
        artist_name="Artist Name",
        score=0.8,
        score_pct=80.0,
        preview_url="https://p.scdn.co/preview.mp3",
    )

    assert '<audio src="https://p.scdn.co/preview.mp3" controls>' in html
    assert has_playable_preview_url("https://p.scdn.co/preview.mp3")
    assert not has_playable_preview_url("nan")


def test_file_size_formatter_uses_compact_units():
    assert format_file_size(512) == "512 B"
    assert format_file_size(2048) == "2.0 KB"
    assert format_file_size(2 * 1024 * 1024) == "2.0 MB"


def test_image_ready_panel_escapes_metadata():
    html = build_image_ready_html(
        source_label="<bad>",
        detail="PNG - 800 x 600 px",
        size_text="2 KB",
    )

    assert "<bad>" not in html
    assert "&lt;bad&gt;" in html
    assert "Ready to analyze" in html


def test_retrieval_summary_escapes_labels_and_shows_profile():
    html = build_retrieval_summary_html(
        {
            "language_label": "<Hindi>",
            "region_label": "Bollywood / Hindi",
            "require_preview": True,
            "prefer_recent": True,
            "boost_indian": True,
            "top_k": 10,
        },
        "PNG - 800 x 600 px",
    )

    assert "<Hindi>" not in html
    assert "&lt;Hindi&gt;" in html
    assert "Playable previews" in html
    assert "Top 10" in html


def test_dashboard_welcome_uses_consistent_empty_state_copy():
    html = build_dashboard_welcome_html()

    assert "Ready for a visual" in html
    assert "Awaiting Visual Input" not in html
    assert "listening profile" in html
    assert "deck-step" not in html
    assert "Add an image or picture URL" not in html


def test_stat_card_separates_value_and_unit_text():
    html = build_stat_card_html("Top Match", "1.023", "match")

    assert '<span class="stat-number">1.023</span>' in html
    assert '<span class="stat-unit" style="color:var(--primary);">match</span>' in html
    assert "1.023match" not in html


def test_stat_card_without_unit_has_no_indented_code_like_markup():
    html = build_stat_card_html("Best Fit", "Excellent match", "")

    assert '<span class="stat-number">Excellent match</span>' in html
    assert "stat-unit" not in html
    assert "\n    </div>" not in html


def test_match_quality_label_uses_human_readable_buckets():
    assert match_quality_label(95) == "Excellent match"
    assert match_quality_label(80) == "Strong match"
    assert match_quality_label(70) == "Good match"
    assert match_quality_label(40) == "Possible match"


def test_normalize_spotify_track_id_rejects_artist_paths():
    assert normalize_spotify_track_id("/artist/asad-amanat-ali") == ""


def test_normalize_spotify_track_id_accepts_track_ids_and_urls():
    track_id = "4z0uvyo23735akUVgkK5iL"

    assert normalize_spotify_track_id(track_id) == track_id
    assert normalize_spotify_track_id(f"https://open.spotify.com/track/{track_id}?si=abc") == track_id
