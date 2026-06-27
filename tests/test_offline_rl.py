"""Tests for offline RL and policy-evaluation utilities."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from offline_rl import (
    build_policy_features,
    estimate_policy_value,
    evaluate_ranked_policy,
    reward_for_action,
    score_linear_policy,
)


def test_reward_for_action_uses_explicit_reward_when_present():
    assert reward_for_action("skip", explicit_reward="0.75") == 0.75


def test_reward_for_action_maps_positive_and_negative_actions():
    assert reward_for_action("selected") > reward_for_action("preview_played")
    assert reward_for_action("dismiss") < 0


def test_estimate_policy_value_reports_logged_and_counterfactual_values():
    interactions = pd.DataFrame(
        {
            "action": ["selected", "skip", "preview_played"],
            "propensity": [0.5, 0.5, 0.25],
            "target_propensity": [0.75, 0.25, 0.25],
        }
    )

    result = estimate_policy_value(interactions)

    assert result["impressions"] == 3
    assert result["average_reward"] > 0
    assert result["ips_value"] is not None
    assert result["snips_value"] is not None
    assert result["effective_sample_size"] > 0
    assert result["warnings"] == []


def test_build_policy_features_marks_language_region_and_media_quality():
    candidates = pd.DataFrame(
        {
            "id": ["global", "tamil"],
            "similarity_score": [0.70, 0.62],
            "india_affinity": [0.0, 1.0],
            "language": ["en", "ta"],
            "region": ["western", "south_indian"],
            "preview": ["", "https://p.scdn.co/preview.mp3"],
            "img": ["", "https://i.scdn.co/image.jpg"],
            "catalog_year": [2024, 2026],
            "popularity": [20, 80],
        }
    )

    features = build_policy_features(
        candidates,
        preferred_language="ta",
        preferred_region="south_indian",
    )

    assert features.loc[1, "language_match"] == 1.0
    assert features.loc[1, "region_match"] == 1.0
    assert features.loc[1, "has_preview"] == 1.0
    assert features.loc[1, "catalog_refresh"] == 1.0
    assert features.loc[1, "popularity"] > features.loc[0, "popularity"]


def test_score_linear_policy_is_offline_and_can_rank_preference_match_first():
    candidates = pd.DataFrame(
        {
            "id": ["global", "hindi"],
            "similarity_score": [0.72, 0.60],
            "india_affinity": [0.0, 1.0],
            "language": ["en", "hi"],
            "region": ["western", "bollywood"],
            "preview": ["", "https://p.scdn.co/preview.mp3"],
        }
    )

    ranked = score_linear_policy(
        candidates,
        weights={"visual_score": 0.1, "language_match": 1.0, "region_match": 1.0},
        preferred_language="hi",
        preferred_region="bollywood",
    )

    assert list(ranked["id"]) == ["hindi", "global"]
    assert "policy_score" in ranked.columns


def test_evaluate_ranked_policy_reports_ndcg_and_preview_share():
    ranked = pd.DataFrame(
        {
            "id": ["wrong", "right"],
            "preview": ["", "https://p.scdn.co/preview.mp3"],
        }
    )

    result = evaluate_ranked_policy(ranked, reward_by_id={"right": 1.0}, top_k=2)

    assert 0 < result["ndcg_at_k"] < 1
    assert result["reciprocal_rank"] == 0.5
    assert result["preview_share_at_k"] == 0.5
