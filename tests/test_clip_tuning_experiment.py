import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from tune_clip_queries import _weighted_score, query_variants


def test_query_variants_include_baseline_and_ensembles():
    case = {
        "prompt": "Rainy romantic evening",
        "preferred_language": "hi",
        "preferred_region": "bollywood",
        "required_moods": ["romantic", "melancholic"],
    }

    variants = query_variants(case)

    assert "baseline" in variants
    assert "ensemble_all" in variants
    assert len(variants["ensemble_all"]) > len(variants["baseline"])
    assert "Indian music recommendation" in variants["music_native"][0]


def test_weighted_score_prioritizes_matching_metrics():
    weak = {
        "avg_language_match_share": 0.1,
        "avg_region_match_share": 0.1,
        "avg_mood_match_share": 0.1,
        "avg_preview_share": 0.9,
        "avg_top_hybrid_score": 0.5,
    }
    strong = {
        "avg_language_match_share": 0.6,
        "avg_region_match_share": 0.6,
        "avg_mood_match_share": 0.6,
        "avg_preview_share": 0.1,
        "avg_top_hybrid_score": 1.0,
    }

    assert _weighted_score(strong) > _weighted_score(weak)
