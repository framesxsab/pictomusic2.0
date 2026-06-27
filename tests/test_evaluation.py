"""Tests for golden recommendation quality checks."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from evaluation import (
    evaluate_catalog_coverage,
    evaluate_ranking_fixtures,
    load_golden_cases,
    run_quality_checks,
)


def test_loads_golden_cases():
    cases = load_golden_cases()
    assert len(cases) >= 8
    assert {case["id"] for case in cases} >= {
        "bollywood_romantic_rain",
        "tamil_festival_energy",
        "punjabi_party_drive",
    }


def test_catalog_coverage_reports_missing_case():
    df = pd.DataFrame(
        {
            "name": ["Only English"],
            "artist": ["Artist"],
            "language": ["en"],
            "region": ["western"],
            "mood_tags": ["happy"],
            "preview": [""],
            "track_url": [""],
        }
    )
    cases = [
        {
            "id": "needs_hindi",
            "required_languages": ["hi"],
            "required_regions": ["bollywood"],
            "required_moods": ["romantic"],
            "min_catalog_matches": 1,
        }
    ]

    result = evaluate_catalog_coverage(df, cases)[0]

    assert not result.passed
    assert "catalog matches 0" in result.failures[0]


def test_ranking_fixtures_pass_current_weights():
    cases = [case for case in load_golden_cases() if case.get("ranking_fixture")]
    results = evaluate_ranking_fixtures(cases)

    assert results
    assert all(result.passed for result in results)
    assert all("policy_ndcg_at_k" in result.metrics for result in results)
    assert all("visible_preview_share" in result.metrics for result in results)


def test_run_quality_checks_can_include_offline_rl_log(monkeypatch, tmp_path):
    dataset = pd.DataFrame(
        {
            "name": ["Hindi Song"],
            "artist": ["Artist"],
            "language": ["hi"],
            "region": ["bollywood"],
            "mood_tags": ["romantic"],
            "preview": ["https://p.scdn.co/preview.mp3"],
            "track_url": ["https://open.spotify.com/track/abc"],
        }
    )
    cases = [
        {
            "id": "small_case",
            "required_languages": ["hi"],
            "required_regions": ["bollywood"],
            "required_moods": ["romantic"],
            "min_catalog_matches": 1,
            "min_preview_matches": 1,
        }
    ]
    log_path = tmp_path / "interactions.csv"
    pd.DataFrame({"action": ["selected"], "propensity": [0.5], "target_propensity": [0.5]}).to_csv(
        log_path,
        index=False,
    )

    monkeypatch.setattr("evaluation.load_golden_cases", lambda path: cases)
    monkeypatch.setattr("evaluation.run_preprocessing", lambda path: dataset)

    summary = run_quality_checks(
        dataset_path="unused.csv",
        golden_path="unused.json",
        interaction_log_path=log_path,
    )

    assert summary["failed"] == 0
    assert summary["offline_rl"]["average_reward"] == 1.0
