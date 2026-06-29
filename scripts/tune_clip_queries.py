"""Offline CLIP query tuning for PictoMusic.

This script tests retrieval-query strategies against the current production
CLIP song embeddings without changing the main application path.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
SCRIPTS_DIR = ROOT / "scripts"
for path in (SRC_DIR, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from compare_siglip_retrieval import (  # noqa: E402
    CaseMetrics,
    _aggregate,
    _case_prompt,
    _norm_set,
    _split_tags,
    build_golden_eval_catalog,
    encode_texts,
)
from config import DATASET_PATH, EMBEDDING_BATCH_SIZE, EMBEDDINGS_PATH  # noqa: E402
from embeddings import build_faiss_index  # noqa: E402
from evaluation import load_golden_cases  # noqa: E402
from preprocess import run_preprocessing  # noqa: E402
from ranking import (  # noqa: E402
    apply_hybrid_ranking,
    apply_visual_intent_guardrails,
    deduplicate_recommendations,
    diversify_recommendations,
    prioritize_preference_matches,
    promote_preview_recommendations,
)


DEFAULT_OUTPUT_DIR = ROOT / "output" / "experiments" / "clip_tuning"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "clip_query_tuning_report.json"
CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"


def _case_values(case: dict[str, Any]) -> dict[str, str]:
    prompt = str(case.get("prompt", "")).strip()
    moods = ", ".join(str(item) for item in case.get("required_moods", []))
    language = str(case.get("preferred_language", "any")).strip()
    region = str(case.get("preferred_region", "any")).strip().replace("_", " ")
    return {
        "prompt": prompt,
        "moods": moods,
        "language": "" if language == "any" else language,
        "region": "" if region == "any" else region,
    }


def query_variants(case: dict[str, Any]) -> dict[str, list[str]]:
    values = _case_values(case)
    prompt = values["prompt"]
    moods = values["moods"]
    language = values["language"]
    region = values["region"]

    style_bits = []
    if language:
        style_bits.append(f"{language} language")
    if region:
        style_bits.append(f"{region} music")
    if moods:
        style_bits.append(f"{moods} mood")
    style_text = ", ".join(style_bits)

    baseline = _case_prompt(case)
    music_native = (
        f"Indian music recommendation for this image: {prompt}. "
        f"Find songs with {style_text}. cinematic, emotional, playlist-ready."
    ).strip()
    listener_intent = (
        f"A listener wants music for {prompt}. "
        f"The best match should feel {moods}. Prefer {style_text}."
    ).strip()
    catalog_style = (
        f"song style tags: {style_text}. visual mood: {prompt}. "
        f"good match for photo-based music discovery."
    ).strip()
    preview_aware = (
        f"playlist-ready Indian song with available streaming preview. "
        f"Scene: {prompt}. Match {style_text}. strong mood fit and recognizable catalog track."
    ).strip()

    return {
        "baseline": [baseline],
        "music_native": [music_native],
        "listener_intent": [listener_intent],
        "catalog_style": [catalog_style],
        "preview_aware": [preview_aware],
        "baseline_music_2_1": [baseline, baseline, music_native],
        "baseline_music_1_1": [baseline, music_native],
        "baseline_intent_2_1": [baseline, baseline, listener_intent],
        "ensemble_music_intent": [music_native, listener_intent],
        "ensemble_all": [baseline, music_native, listener_intent, catalog_style],
    }


def _embed_variant_queries(
    cases: list[dict[str, Any]],
    *,
    batch_size: int,
) -> dict[str, np.ndarray]:
    variant_names = list(query_variants(cases[0]).keys())
    result: dict[str, list[np.ndarray]] = {name: [] for name in variant_names}
    flat_texts: list[str] = []
    flat_index: list[tuple[str, int]] = []

    for case_index, case in enumerate(cases):
        for variant_name, texts in query_variants(case).items():
            for text in texts:
                flat_index.append((variant_name, case_index))
                flat_texts.append(text)

    embeddings = encode_texts(
        flat_texts,
        kind="clip",
        model_name=CLIP_MODEL_NAME,
        batch_size=batch_size,
    )

    scratch: dict[str, dict[int, list[np.ndarray]]] = {name: {} for name in variant_names}
    for embedding, (variant_name, case_index) in zip(embeddings, flat_index):
        scratch[variant_name].setdefault(case_index, []).append(embedding)

    final: dict[str, np.ndarray] = {}
    for variant_name in variant_names:
        case_embeddings = []
        for case_index in range(len(cases)):
            stacked = np.vstack(scratch[variant_name][case_index]).astype(np.float32)
            pooled = stacked.mean(axis=0, keepdims=True)
            pooled = pooled / np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-6)
            case_embeddings.append(pooled[0])
        final[variant_name] = np.vstack(case_embeddings)
    return final


def _load_clip_embeddings_for_df(df: pd.DataFrame) -> np.ndarray:
    full_embeddings = np.load(EMBEDDINGS_PATH, allow_pickle=False)
    if "_source_catalog_index" in df.columns:
        return full_embeddings[df["_source_catalog_index"].astype(int).to_numpy()]
    return full_embeddings[: len(df)]


def _share(mask: pd.Series) -> float:
    return round(float(mask.mean()), 4) if len(mask) else 0.0


def _has_http(value: object) -> bool:
    return str(value or "").strip().lower().startswith(("http://", "https://"))


def _metadata_backfill(
    *,
    df: pd.DataFrame,
    case: dict[str, Any],
    existing_indices: set[int],
    limit: int,
) -> pd.DataFrame:
    languages = _norm_set(case.get("required_languages", []))
    regions = _norm_set(case.get("required_regions", []))
    moods = _norm_set(case.get("required_moods", []))

    mask = pd.Series(True, index=df.index)
    if languages and "language" in df.columns:
        mask &= df["language"].fillna("").astype(str).str.lower().isin(languages)
    if regions and "region" in df.columns:
        mask &= df["region"].fillna("").astype(str).str.lower().isin(regions)
    if moods and "mood_tags" in df.columns:
        mask &= df["mood_tags"].map(lambda value: bool(_split_tags(value) & moods))
    mask &= ~df.index.isin(existing_indices)

    candidates = df[mask].copy()
    if candidates.empty:
        return candidates

    candidates["_has_preview"] = candidates.get("preview", "").map(_has_http) if "preview" in candidates.columns else False
    candidates["_popularity"] = pd.to_numeric(candidates.get("popularity", 0), errors="coerce").fillna(0)
    candidates["_catalog_year"] = pd.to_numeric(candidates.get("catalog_year", 0), errors="coerce").fillna(0)
    candidates.sort_values(
        ["_has_preview", "_catalog_year", "_popularity"],
        ascending=[False, False, False],
        inplace=True,
    )
    return candidates.head(limit).drop(
        columns=["_has_preview", "_popularity", "_catalog_year"],
        errors="ignore",
    )


def _evaluate_case_strategy(
    *,
    engine_name: str,
    query_embedding: np.ndarray,
    index,
    df: pd.DataFrame,
    case: dict[str, Any],
    candidate_count: int,
    top_k: int,
    app_like: bool,
    backfill_limit: int = 0,
    preview_margin: float = 0.12,
) -> CaseMetrics:
    distances, indices = index.search(query_embedding.astype("float32"), candidate_count)
    vector_indices = [int(idx) for idx in indices[0]]
    candidates = df.iloc[vector_indices].copy()
    scores = distances[0].astype(float)
    candidates["visual_score"] = scores
    candidates["similarity_score"] = scores
    candidates["_retrieval_source"] = "clip"

    if backfill_limit > 0:
        backfill = _metadata_backfill(
            df=df,
            case=case,
            existing_indices=set(candidates.index),
            limit=backfill_limit,
        )
        if not backfill.empty:
            score_floor = float(np.percentile(scores, 60)) if len(scores) else 0.35
            backfill = backfill.copy()
            backfill["visual_score"] = score_floor
            backfill["similarity_score"] = score_floor
            backfill["_retrieval_source"] = "metadata_backfill"
            candidates = pd.concat([candidates, backfill], ignore_index=False)

    if app_like:
        candidates = apply_visual_intent_guardrails(
            candidates,
            detected_themes=[],
            mood_keywords=case.get("required_moods", []),
        )

    ranked = apply_hybrid_ranking(
        candidates,
        preferred_language=case.get("preferred_language", "any"),
        preferred_region=case.get("preferred_region", "any"),
        prefer_recent=True,
        require_preview=False,
        boost_indian=True,
    )
    ranked = deduplicate_recommendations(ranked)
    if app_like:
        ranked = prioritize_preference_matches(
            ranked,
            preferred_language=case.get("preferred_language", "any"),
            preferred_region=case.get("preferred_region", "any"),
        )
    ranked = promote_preview_recommendations(
        ranked,
        target_size=top_k,
        importance_margin=preview_margin,
    )
    if app_like:
        ranked = prioritize_preference_matches(
            ranked,
            preferred_language=case.get("preferred_language", "any"),
            preferred_region=case.get("preferred_region", "any"),
        )
        ranked = diversify_recommendations(ranked, target_size=top_k)
    visible = ranked.head(top_k)

    languages = _norm_set(case.get("required_languages", []))
    regions = _norm_set(case.get("required_regions", []))
    moods = _norm_set(case.get("required_moods", []))
    top_row = visible.iloc[0].to_dict() if not visible.empty else {}

    language_share = (
        _share(visible["language"].fillna("").astype(str).str.lower().isin(languages))
        if languages and "language" in visible.columns
        else 0.0
    )
    region_share = (
        _share(visible["region"].fillna("").astype(str).str.lower().isin(regions))
        if regions and "region" in visible.columns
        else 0.0
    )
    mood_share = (
        _share(visible["mood_tags"].map(lambda value: bool(_split_tags(value) & moods)))
        if moods and "mood_tags" in visible.columns
        else 0.0
    )
    preview_share = (
        _share(visible["preview"].astype(str).str.startswith("http"))
        if "preview" in visible.columns
        else 0.0
    )

    return CaseMetrics(
        engine=engine_name,
        case_id=str(case["id"]),
        top_k=top_k,
        candidate_count=int(candidate_count),
        language_match_share=language_share,
        region_match_share=region_share,
        mood_match_share=mood_share,
        preview_share=preview_share,
        mean_visual_score=round(float(visible["visual_score"].mean()), 4)
        if "visual_score" in visible.columns and not visible.empty
        else 0.0,
        top_visual_score=round(float(top_row.get("visual_score", 0.0)), 4),
        top_hybrid_score=round(float(top_row.get("hybrid_score", 0.0)), 4),
        top_name=str(top_row.get("name", "")),
        top_artist=str(top_row.get("artist", "")),
        top_language=str(top_row.get("language", "")),
        top_region=str(top_row.get("region", "")),
    )


def _weighted_score(summary: dict[str, Any]) -> float:
    return round(
        float(summary.get("avg_language_match_share", 0.0)) * 0.25
        + float(summary.get("avg_region_match_share", 0.0)) * 0.25
        + float(summary.get("avg_mood_match_share", 0.0)) * 0.25
        + float(summary.get("avg_preview_share", 0.0)) * 0.10
        + float(summary.get("avg_top_hybrid_score", 0.0)) * 0.15,
        4,
    )


def run_experiment(
    *,
    df: pd.DataFrame,
    cases: list[dict[str, Any]],
    batch_size: int,
    candidate_count: int,
    top_k: int,
    only: set[str] | None = None,
) -> dict[str, Any]:
    clip_embeddings = _load_clip_embeddings_for_df(df)
    index = build_faiss_index(clip_embeddings)
    if index is None:
        raise RuntimeError("Could not build CLIP FAISS index")

    query_embeddings = _embed_variant_queries(cases, batch_size=batch_size)
    safe_candidate_count = min(candidate_count, len(df))

    metrics: list[CaseMetrics] = []
    for variant_name, embeddings in query_embeddings.items():
        if only is not None and variant_name not in only:
            continue
        for case_index, case in enumerate(cases):
            metrics.append(
                _evaluate_case_strategy(
                    engine_name=variant_name,
                    query_embedding=embeddings[case_index : case_index + 1],
                    index=index,
                    df=df,
                    case=case,
                    candidate_count=safe_candidate_count,
                    top_k=top_k,
                    app_like=False,
                )
            )

    strategy_specs = {
        "app_baseline": {
            "query": "baseline",
            "app_like": True,
            "backfill_limit": 0,
            "preview_margin": 0.12,
        },
        "app_preview_aware": {
            "query": "preview_aware",
            "app_like": True,
            "backfill_limit": 0,
            "preview_margin": 0.12,
        },
        "app_baseline_preview_margin": {
            "query": "baseline",
            "app_like": True,
            "backfill_limit": 0,
            "preview_margin": 0.35,
        },
        "hybrid_backfill": {
            "query": "baseline",
            "app_like": True,
            "backfill_limit": 250,
            "preview_margin": 0.35,
        },
        "hybrid_backfill_preview_query": {
            "query": "preview_aware",
            "app_like": True,
            "backfill_limit": 250,
            "preview_margin": 0.35,
        },
        "hybrid_backfill_aggressive": {
            "query": "preview_aware",
            "app_like": True,
            "backfill_limit": 500,
            "preview_margin": 0.6,
        },
    }
    for strategy_name, spec in strategy_specs.items():
        if only is not None and strategy_name not in only:
            continue
        embeddings = query_embeddings[spec["query"]]
        for case_index, case in enumerate(cases):
            metrics.append(
                _evaluate_case_strategy(
                    engine_name=strategy_name,
                    query_embedding=embeddings[case_index : case_index + 1],
                    index=index,
                    df=df,
                    case=case,
                    candidate_count=safe_candidate_count,
                    top_k=top_k,
                    app_like=bool(spec["app_like"]),
                    backfill_limit=int(spec["backfill_limit"]),
                    preview_margin=float(spec["preview_margin"]),
                )
            )

    engine_names = [
        name for name in list(query_embeddings) + list(strategy_specs)
        if only is None or name in only
    ]
    summaries = {
        variant_name: _aggregate(
            [metric for metric in metrics if metric.engine == variant_name]
        )
        for variant_name in engine_names
    }
    weighted_scores = {
        variant_name: _weighted_score(summary)
        for variant_name, summary in summaries.items()
    }
    baseline_score = weighted_scores.get("baseline", next(iter(weighted_scores.values())))
    app_baseline_score = weighted_scores.get("app_baseline", baseline_score)
    best_variant = max(weighted_scores, key=weighted_scores.get)
    deltas = {
        variant_name: round(score - baseline_score, 4)
        for variant_name, score in weighted_scores.items()
    }
    app_deltas = {
        variant_name: round(score - app_baseline_score, 4)
        for variant_name, score in weighted_scores.items()
    }

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset_rows": int(len(df)),
        "case_count": int(len(cases)),
        "candidate_count": int(safe_candidate_count),
        "top_k": int(top_k),
        "summaries": summaries,
        "weighted_scores": weighted_scores,
        "deltas_vs_baseline": deltas,
        "deltas_vs_app_baseline": app_deltas,
        "best_variant": best_variant,
        "recommendation": (
            "ship_candidate_after_main_engine_smoke"
            if best_variant != "baseline" and app_deltas[best_variant] >= 0.02
            else "keep_current_query"
        ),
        "case_metrics": [asdict(metric) for metric in metrics],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=DATASET_PATH)
    parser.add_argument("--golden", default=str(ROOT / "evaluation" / "golden_recommendations.json"))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--batch-size", type=int, default=EMBEDDING_BATCH_SIZE)
    parser.add_argument("--candidate-count", type=int, default=50000)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--golden-per-case", type=int, default=160)
    parser.add_argument("--golden-distractors", type=int, default=1000)
    parser.add_argument("--full-catalog", action="store_true")
    parser.add_argument("--only", default="", help="Comma-separated strategy names to evaluate")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print("Loading catalog and golden cases...", flush=True)
    df = run_preprocessing(existing_csv=args.dataset, output_path=None)
    cases = load_golden_cases(args.golden)
    if not args.full_catalog:
        df = build_golden_eval_catalog(
            df,
            cases,
            per_case=args.golden_per_case,
            distractors=args.golden_distractors,
        )
    report = run_experiment(
        df=df,
        cases=cases,
        batch_size=args.batch_size,
        candidate_count=args.candidate_count,
        top_k=args.top_k,
        only={item.strip() for item in args.only.split(",") if item.strip()} or None,
    )
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")

    print(json.dumps({
        "weighted_scores": report["weighted_scores"],
        "deltas_vs_baseline": report["deltas_vs_baseline"],
        "deltas_vs_app_baseline": report["deltas_vs_app_baseline"],
        "best_variant": report["best_variant"],
        "recommendation": report["recommendation"],
        "report": str(report_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
