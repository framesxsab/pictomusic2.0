"""Tests for hybrid ranking behavior."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ranking import (
    apply_hybrid_ranking,
    deduplicate_recommendations,
    promote_preview_recommendations,
    song_identity_key,
    parse_release_year,
)


def test_parse_release_year_from_date():
    assert parse_release_year("2024-02-16") == 2024


def test_parse_release_year_rejects_invalid_future():
    assert parse_release_year("2099-01-01") is None


def test_hybrid_ranking_boosts_india_language_and_preview():
    results = pd.DataFrame(
        {
            "name": ["Global song", "Tamil song"],
            "artist": ["Global Artist", "Anirudh"],
            "similarity_score": [0.50, 0.47],
            "india_affinity": [0.0, 1.0],
            "language": ["en", "ta"],
            "region": ["western", "south_indian"],
            "preview": ["", "https://p.scdn.co/preview.mp3"],
            "img": ["", "https://i.scdn.co/image.jpg"],
            "release_year": [2020, 2024],
        }
    )

    ranked = apply_hybrid_ranking(
        results,
        preferred_language="ta",
        preferred_region="south_indian",
        prefer_recent=True,
    )

    assert ranked.iloc[0]["name"] == "Tamil song"
    assert ranked.iloc[0]["hybrid_score"] > ranked.iloc[0]["visual_score"]


def test_hybrid_ranking_can_require_preview():
    results = pd.DataFrame(
        {
            "name": ["No preview", "Has preview"],
            "similarity_score": [0.9, 0.2],
            "preview": ["", "https://p.scdn.co/preview.mp3"],
        }
    )

    ranked = apply_hybrid_ranking(results, require_preview=True)

    assert list(ranked["name"]) == ["Has preview"]


def test_hybrid_ranking_boosts_2026_catalog_refresh():
    results = pd.DataFrame(
        {
            "name": ["Older source", "2026 refresh"],
            "similarity_score": [0.30, 0.30],
            "catalog_year": [2024, 2026],
        }
    )

    ranked = apply_hybrid_ranking(results, prefer_recent=True)

    assert ranked.iloc[0]["name"] == "2026 refresh"


def test_deduplicate_recommendations_prefers_preview_variant():
    results = pd.DataFrame(
        {
            "id": ["no_preview", "with_preview", "other"],
            "name": ["Same Song (From Film)", "Same Song", "Other Song"],
            "artist": ["Singer One, Singer Two", "Singer Two, Singer One", "Other Artist"],
            "hybrid_score": [0.84, 0.78, 0.70],
            "preview": ["", "https://p.scdn.co/preview.mp3", ""],
            "img": ["https://i.scdn.co/a.jpg", "https://i.scdn.co/b.jpg", ""],
            "spotify_id": ["a", "b", "c"],
        }
    )

    deduped = deduplicate_recommendations(results)
    keys = deduped.apply(song_identity_key, axis=1)

    assert len(deduped) == 2
    assert not keys.duplicated().any()
    assert "with_preview" in set(deduped["id"])
    assert "no_preview" not in set(deduped["id"])


def test_preview_promotion_favors_previews_but_keeps_important_match():
    results = pd.DataFrame(
        {
            "id": [
                "important_non_preview",
                "close_non_preview_one",
                "close_non_preview_two",
                "preview_close_one",
                "preview_close_two",
            ],
            "name": [
                "Important",
                "Close One",
                "Close Two",
                "Preview One",
                "Preview Two",
            ],
            "artist": ["A", "B", "C", "D", "E"],
            "hybrid_score": [0.94, 0.91, 0.89, 0.86, 0.84],
            "preview": [
                "",
                "",
                "",
                "https://p.scdn.co/one.mp3",
                "https://p.scdn.co/two.mp3",
            ],
        }
    )

    promoted = promote_preview_recommendations(results, target_size=3)
    visible = promoted.head(3)

    assert visible.iloc[0]["id"] == "important_non_preview"
    assert visible["preview"].astype(str).str.startswith("http").sum() == 2


def test_hybrid_ranking_boosts_india_affinity_conditionally():
    results = pd.DataFrame(
        {
            "name": ["Global song", "Tamil song"],
            "artist": ["Global Artist", "Anirudh"],
            "similarity_score": [0.50, 0.47],
            "india_affinity": [0.0, 1.0],
            "language": ["en", "ta"],
            "region": ["western", "south_indian"],
            "preview": ["", ""],
            "img": ["", ""],
            "release_year": [2020, 2024],
        }
    )

    # With boost_indian=False
    ranked_no_boost = apply_hybrid_ranking(
        results,
        boost_indian=False,
        prefer_recent=False,
    )
    # The global song has higher similarity, and no india boost is applied, so it stays first
    assert ranked_no_boost.iloc[0]["name"] == "Global song"

    # With boost_indian=True
    ranked_boost = apply_hybrid_ranking(
        results,
        boost_indian=True,
        prefer_recent=False,
    )
    # The Tamil song has lower similarity but high india affinity boost, so it goes first
    assert ranked_boost.iloc[0]["name"] == "Tamil song"
