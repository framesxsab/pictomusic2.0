"""Tests for golden recommendation quality checks."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from evaluation import (
    evaluate_catalog_coverage,
    evaluate_ranking_fixtures,
    load_golden_cases,
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
