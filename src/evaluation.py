"""Golden quality checks for PictoMusic recommendation behavior."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import BASE_DIR, DATASET_PATH
from preprocess import run_preprocessing
from ranking import (
    apply_hybrid_ranking,
    apply_visual_intent_guardrails,
    deduplicate_recommendations,
    promote_preview_recommendations,
    song_identity_key,
)


DEFAULT_GOLDEN_PATH = BASE_DIR / "evaluation" / "golden_recommendations.json"


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    passed: bool
    metrics: dict[str, Any]
    failures: list[str]


def load_golden_cases(path: str | Path = DEFAULT_GOLDEN_PATH) -> list[dict[str, Any]]:
    """Load the curated golden recommendation cases."""
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    cases = payload.get("cases", [])
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"No golden cases found in {path}")
    return cases


def _norm_set(values: list[str]) -> set[str]:
    return {str(value).strip().lower() for value in values if str(value).strip()}


def _split_tags(value: object) -> set[str]:
    return _norm_set(str(value or "").split(","))


def _case_mask(df: pd.DataFrame, case: dict[str, Any]) -> pd.Series:
    mask = pd.Series(True, index=df.index)

    languages = _norm_set(case.get("required_languages", []))
    if languages and "language" in df.columns:
        mask &= df["language"].fillna("").astype(str).str.lower().isin(languages)

    regions = _norm_set(case.get("required_regions", []))
    if regions and "region" in df.columns:
        mask &= df["region"].fillna("").astype(str).str.lower().isin(regions)

    moods = _norm_set(case.get("required_moods", []))
    if moods and "mood_tags" in df.columns:
        mask &= df["mood_tags"].map(lambda value: bool(_split_tags(value) & moods))

    return mask


def evaluate_catalog_coverage(
    df: pd.DataFrame,
    cases: list[dict[str, Any]],
) -> list[CaseResult]:
    """Check that the real corpus has enough candidates for each golden scenario."""
    results: list[CaseResult] = []
    for case in cases:
        if case.get("catalog_check", True) is False:
            continue

        matches = df[_case_mask(df, case)]
        preview_matches = 0
        if "preview" in matches.columns:
            preview_matches = int(matches["preview"].astype(str).str.startswith("http").sum())
        link_matches = 0
        if "track_url" in matches.columns:
            link_matches = int(matches["track_url"].astype(str).str.startswith("http").sum())

        min_catalog = int(case.get("min_catalog_matches", 1))
        min_preview = int(case.get("min_preview_matches", 0))
        min_links = int(case.get("min_link_matches", 0))
        failures = []
        if len(matches) < min_catalog:
            failures.append(
                f"catalog matches {len(matches)} below required {min_catalog}"
            )
        if preview_matches < min_preview:
            failures.append(
                f"preview matches {preview_matches} below required {min_preview}"
            )
        if link_matches < min_links:
            failures.append(
                f"track links {link_matches} below required {min_links}"
            )

        results.append(
            CaseResult(
                case_id=case["id"],
                passed=not failures,
                metrics={
                    "catalog_matches": int(len(matches)),
                    "preview_matches": preview_matches,
                    "link_matches": link_matches,
                    "min_catalog_matches": min_catalog,
                    "min_preview_matches": min_preview,
                    "min_link_matches": min_links,
                },
                failures=failures,
            )
        )
    return results


def evaluate_ranking_fixtures(cases: list[dict[str, Any]]) -> list[CaseResult]:
    """Check deterministic ranking fixtures embedded in the golden cases."""
    results: list[CaseResult] = []
    for case in cases:
        fixture = case.get("ranking_fixture")
        if not fixture:
            continue

        candidates = pd.DataFrame(fixture["candidates"])
        if "similarity_score" in candidates.columns and "visual_score" not in candidates.columns:
            candidates["visual_score"] = candidates["similarity_score"]
        target_size = int(fixture.get("target_size", len(candidates)))
        candidates = apply_visual_intent_guardrails(
            candidates,
            detected_themes=fixture.get("detected_themes", []),
            mood_keywords=fixture.get("mood_keywords", []),
        )
        ranked = apply_hybrid_ranking(
            candidates,
            preferred_language=case.get("preferred_language", "any"),
            preferred_region=case.get("preferred_region", "any"),
            prefer_recent=True,
            require_preview=False,
        )
        ranked = deduplicate_recommendations(ranked)
        ranked = promote_preview_recommendations(ranked, target_size=target_size)
        visible = ranked.head(target_size)

        actual_top = str(ranked.iloc[0]["id"]) if not ranked.empty else ""
        expected_top = str(fixture["expected_top"])
        failures = []
        if actual_top != expected_top:
            failures.append(f"top result {actual_top!r} != expected {expected_top!r}")

        min_preview_count = fixture.get("min_preview_count")
        preview_count = 0
        if "preview" in visible.columns:
            preview_count = int(visible["preview"].astype(str).str.startswith("http").sum())
        if min_preview_count is not None and preview_count < int(min_preview_count):
            failures.append(
                f"visible preview count {preview_count} below required {min_preview_count}"
            )

        duplicate_count = 0
        if not visible.empty:
            keys = visible.apply(song_identity_key, axis=1)
            duplicate_count = int(keys.duplicated().sum())
        if fixture.get("require_unique", True) and duplicate_count:
            failures.append(f"visible duplicate songs found: {duplicate_count}")

        top_row = ranked.iloc[0].to_dict() if not ranked.empty else {}
        results.append(
            CaseResult(
                case_id=case["id"],
                passed=not failures,
                metrics={
                    "expected_top": expected_top,
                    "actual_top": actual_top,
                    "target_size": target_size,
                    "visible_preview_count": preview_count,
                    "visible_duplicate_count": duplicate_count,
                    "top_hybrid_score": round(float(top_row.get("hybrid_score", 0.0)), 4),
                    "top_visual_score": round(float(top_row.get("visual_score", 0.0)), 4),
                },
                failures=failures,
            )
        )
    return results


def summarize_results(results: list[CaseResult]) -> dict[str, Any]:
    passed = sum(1 for result in results if result.passed)
    return {
        "passed": passed,
        "failed": len(results) - passed,
        "total": len(results),
        "results": [
            {
                "case_id": result.case_id,
                "passed": result.passed,
                "metrics": result.metrics,
                "failures": result.failures,
            }
            for result in results
        ],
    }


def run_quality_checks(
    dataset_path: str = DATASET_PATH,
    golden_path: str | Path = DEFAULT_GOLDEN_PATH,
) -> dict[str, Any]:
    cases = load_golden_cases(golden_path)
    df = run_preprocessing(dataset_path)
    catalog_results = evaluate_catalog_coverage(df, cases)
    ranking_results = evaluate_ranking_fixtures(cases)
    all_results = catalog_results + ranking_results
    summary = summarize_results(all_results)
    summary["catalog_rows"] = int(len(df))
    summary["golden_cases"] = int(len(cases))
    return summary


def _print_summary(summary: dict[str, Any]) -> None:
    print(
        f"Golden checks: {summary['passed']}/{summary['total']} passed "
        f"({summary['failed']} failed), catalog rows: {summary['catalog_rows']}"
    )
    for result in summary["results"]:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{status} {result['case_id']}: {result['metrics']}")
        for failure in result["failures"]:
            print(f"  - {failure}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PictoMusic golden quality checks.")
    parser.add_argument("--dataset", default=DATASET_PATH, help="Path to Music.csv")
    parser.add_argument("--golden", default=str(DEFAULT_GOLDEN_PATH), help="Path to golden JSON")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    summary = run_quality_checks(dataset_path=args.dataset, golden_path=args.golden)
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        _print_summary(summary)
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
