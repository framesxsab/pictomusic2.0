"""Tests for UI HTML builders."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ui.components import build_song_card_html


def test_song_card_without_tags_does_not_indent_score_as_markdown_code():
    html = build_song_card_html(
        idx=0,
        song_name="Juke Jam (feat. Justin Bieber & Towkio)",
        artist_name="Chance the Rapper",
        score=0.554,
        score_pct=80.0,
        visual_score=0.459,
    )

    assert '<div class="score-container">' in html
    assert "\n    <div class=\"score-container\">" not in html
    assert "&amp;" in html


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
