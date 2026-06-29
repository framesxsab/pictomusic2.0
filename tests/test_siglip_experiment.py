import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import pandas as pd

from compare_siglip_retrieval import CaseMetrics, _aggregate, build_golden_eval_catalog


def test_siglip_experiment_aggregate_keeps_engine_metrics_separate():
    metrics = [
        CaseMetrics(
            engine="clip",
            case_id="case_a",
            top_k=3,
            candidate_count=20,
            language_match_share=0.3,
            region_match_share=0.4,
            mood_match_share=0.5,
            preview_share=0.6,
            mean_visual_score=0.2,
            top_visual_score=0.7,
            top_hybrid_score=1.1,
            top_name="Clip Song",
            top_artist="Clip Artist",
            top_language="hi",
            top_region="bollywood",
        ),
        CaseMetrics(
            engine="clip",
            case_id="case_b",
            top_k=3,
            candidate_count=20,
            language_match_share=0.5,
            region_match_share=0.6,
            mood_match_share=0.7,
            preview_share=0.8,
            mean_visual_score=0.3,
            top_visual_score=0.9,
            top_hybrid_score=1.3,
            top_name="Clip Song 2",
            top_artist="Clip Artist 2",
            top_language="ta",
            top_region="south_indian",
        ),
    ]

    summary = _aggregate(metrics)

    assert summary["cases"] == 2
    assert summary["avg_language_match_share"] == 0.4
    assert summary["avg_region_match_share"] == 0.5
    assert summary["avg_mood_match_share"] == 0.6
    assert summary["avg_preview_share"] == 0.7
    assert summary["avg_top_hybrid_score"] == 1.2


def test_golden_eval_catalog_preserves_source_indices():
    df = pd.DataFrame(
        {
            "language": ["hi", "ta", "en"],
            "region": ["bollywood", "south_indian", "western"],
            "mood_tags": ["romantic,calm", "happy,danceable", "focus"],
            "popularity": [80, 70, 60],
        },
        index=[10, 20, 30],
    )
    cases = [
        {
            "id": "romance",
            "required_languages": ["hi"],
            "required_regions": ["bollywood"],
            "required_moods": ["romantic"],
        }
    ]

    subset = build_golden_eval_catalog(df, cases, per_case=1, distractors=1)

    assert "_source_catalog_index" in subset.columns
    assert 10 in set(subset["_source_catalog_index"])
    assert len(subset) == 2
