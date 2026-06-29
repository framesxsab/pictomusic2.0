"""Offline CLIP vs SigLIP retrieval experiment for PictoMusic.

This script is intentionally isolated from production artifacts. It writes all
experiment caches and reports under output/experiments/ unless overridden.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DATASET_PATH, EMBEDDING_BATCH_SIZE, EMBEDDINGS_PATH
from embeddings import build_faiss_index, fingerprint_texts, normalize_embeddings
from evaluation import load_golden_cases
from preprocess import build_enhanced_description, run_preprocessing
from ranking import (
    apply_hybrid_ranking,
    deduplicate_recommendations,
    promote_preview_recommendations,
)


DEFAULT_SIGLIP_MODEL = "google/siglip-base-patch16-224"
DEFAULT_OUTPUT_DIR = ROOT / "output" / "experiments" / "siglip"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "siglip_vs_clip_report.json"


@dataclass(frozen=True)
class EngineSpec:
    name: str
    model_name: str
    embeddings_path: Path
    manifest_path: Path
    kind: str


@dataclass
class CaseMetrics:
    engine: str
    case_id: str
    top_k: int
    candidate_count: int
    language_match_share: float
    region_match_share: float
    mood_match_share: float
    preview_share: float
    mean_visual_score: float
    top_visual_score: float
    top_hybrid_score: float
    top_name: str
    top_artist: str
    top_language: str
    top_region: str


def _norm_set(values: Iterable[Any]) -> set[str]:
    return {str(value).strip().lower() for value in values if str(value).strip()}


def _split_tags(value: object) -> set[str]:
    return _norm_set(str(value or "").split(","))


def _share(mask: pd.Series) -> float:
    return round(float(mask.mean()), 4) if len(mask) else 0.0


def _read_manifest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else None


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _manifest_matches(
    manifest: dict[str, Any] | None,
    *,
    model_name: str,
    text_fingerprint: str,
    dataset_size: int,
) -> bool:
    if not manifest:
        return False
    return (
        manifest.get("model_name") == model_name
        and manifest.get("text_fingerprint") == text_fingerprint
        and manifest.get("dataset_size") == dataset_size
    )


def _load_torch_and_transformers():
    import torch
    from transformers import AutoModel, AutoProcessor, CLIPModel, CLIPProcessor

    return torch, AutoModel, AutoProcessor, CLIPModel, CLIPProcessor


def _pool_siglip_features(outputs, attention_mask, torch):
    token_embeddings = outputs.last_hidden_state
    mask = attention_mask.unsqueeze(-1).to(token_embeddings.dtype)
    summed = (token_embeddings * mask).sum(dim=1)
    counts = mask.sum(dim=1).clamp(min=1.0)
    return summed / counts


def encode_texts(
    texts: list[str],
    *,
    kind: str,
    model_name: str,
    batch_size: int,
) -> np.ndarray:
    torch, AutoModel, AutoProcessor, CLIPModel, CLIPProcessor = _load_torch_and_transformers()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if kind == "clip":
        model = CLIPModel.from_pretrained(model_name).to(device)
        processor = CLIPProcessor.from_pretrained(model_name)
    elif kind == "siglip":
        model = AutoModel.from_pretrained(model_name).to(device)
        processor = AutoProcessor.from_pretrained(model_name)
    else:
        raise ValueError(f"Unknown engine kind: {kind}")

    model.eval()
    all_embeddings = []
    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            inputs = processor(
                text=batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
            )
            inputs = {key: value.to(device) for key, value in inputs.items()}
            if kind == "clip":
                features = model.get_text_features(**inputs)
            elif hasattr(model, "get_text_features"):
                features = model.get_text_features(**inputs)
            else:
                outputs = model.text_model(**inputs)
                features = _pool_siglip_features(outputs, inputs["attention_mask"], torch)
                if hasattr(model, "text_projection"):
                    features = model.text_projection(features)
            features = features / features.norm(p=2, dim=-1, keepdim=True)
            all_embeddings.append(features.cpu())
            print(
                f"{kind}: encoded {min(start + batch_size, len(texts))}/{len(texts)} texts",
                flush=True,
            )
    return torch.cat(all_embeddings, dim=0).numpy()


def load_or_build_experiment_embeddings(
    spec: EngineSpec,
    *,
    texts: list[str],
    batch_size: int,
    force: bool,
) -> np.ndarray:
    text_fingerprint = fingerprint_texts(texts)
    manifest = _read_manifest(spec.manifest_path)
    if not force and spec.embeddings_path.exists() and _manifest_matches(
        manifest,
        model_name=spec.model_name,
        text_fingerprint=text_fingerprint,
        dataset_size=len(texts),
    ):
        return np.load(spec.embeddings_path, allow_pickle=False)

    embeddings = encode_texts(
        texts,
        kind=spec.kind,
        model_name=spec.model_name,
        batch_size=batch_size,
    )
    saved = embeddings.astype(np.float16)
    spec.embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(spec.embeddings_path, saved)
    _write_manifest(
        spec.manifest_path,
        {
            "dataset_size": len(texts),
            "embedding_dtype": str(saved.dtype),
            "embedding_shape": [int(value) for value in saved.shape],
            "engine": spec.name,
            "model_name": spec.model_name,
            "text_fingerprint": text_fingerprint,
            "version": 1,
        },
    )
    return saved


def _case_prompt(case: dict[str, Any]) -> str:
    parts = [str(case.get("prompt", "")).strip()]
    moods = case.get("required_moods", [])
    if moods:
        parts.append("music mood: " + ", ".join(str(item) for item in moods))
    language = str(case.get("preferred_language", "any")).strip()
    region = str(case.get("preferred_region", "any")).strip()
    if language and language != "any":
        parts.append(f"preferred language: {language}")
    if region and region != "any":
        parts.append(f"preferred region: {region}")
    return ". ".join(part for part in parts if part)


def _case_mask(df: pd.DataFrame, case: dict[str, Any]) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    languages = _norm_set(case.get("required_languages", []))
    regions = _norm_set(case.get("required_regions", []))
    moods = _norm_set(case.get("required_moods", []))
    if languages and "language" in df.columns:
        mask &= df["language"].fillna("").astype(str).str.lower().isin(languages)
    if regions and "region" in df.columns:
        mask &= df["region"].fillna("").astype(str).str.lower().isin(regions)
    if moods and "mood_tags" in df.columns:
        mask &= df["mood_tags"].map(lambda value: bool(_split_tags(value) & moods))
    return mask


def build_golden_eval_catalog(
    df: pd.DataFrame,
    cases: list[dict[str, Any]],
    *,
    per_case: int,
    distractors: int,
) -> pd.DataFrame:
    """Create a deterministic, relevant comparison corpus for CPU experiments."""
    selected_indices: set[int] = set()
    for case in cases:
        matches = df[_case_mask(df, case)]
        if matches.empty:
            continue
        priority_cols = []
        if "popularity" in matches.columns:
            priority_cols.append("popularity")
        if "catalog_year" in matches.columns:
            priority_cols.append("catalog_year")
        if priority_cols:
            matches = matches.sort_values(priority_cols, ascending=False)
        selected_indices.update(matches.head(per_case).index.tolist())

    available_distractors = df[~df.index.isin(selected_indices)]
    if distractors > 0 and not available_distractors.empty:
        sampled = available_distractors.sample(
            n=min(distractors, len(available_distractors)),
            random_state=42,
        )
        selected_indices.update(sampled.index.tolist())

    if not selected_indices:
        raise ValueError("Golden evaluation corpus is empty.")
    subset = df.loc[sorted(selected_indices)].copy()
    subset["_source_catalog_index"] = subset.index.astype(int)
    return subset.reset_index(drop=True)


def _evaluate_case(
    *,
    engine_name: str,
    query_embedding: np.ndarray,
    index,
    df: pd.DataFrame,
    case: dict[str, Any],
    candidate_count: int,
    top_k: int,
) -> CaseMetrics:
    distances, indices = index.search(query_embedding.astype("float32"), candidate_count)
    candidates = df.iloc[indices[0]].copy()
    scores = distances[0].astype(float)
    candidates["visual_score"] = scores
    candidates["similarity_score"] = scores
    ranked = apply_hybrid_ranking(
        candidates,
        preferred_language=case.get("preferred_language", "any"),
        preferred_region=case.get("preferred_region", "any"),
        prefer_recent=True,
        require_preview=False,
        boost_indian=True,
    )
    ranked = deduplicate_recommendations(ranked)
    ranked = promote_preview_recommendations(ranked, target_size=top_k)
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


def _aggregate(metrics: list[CaseMetrics]) -> dict[str, Any]:
    if not metrics:
        return {}
    frame = pd.DataFrame([asdict(item) for item in metrics])
    return {
        "cases": int(len(frame)),
        "avg_language_match_share": round(float(frame["language_match_share"].mean()), 4),
        "avg_region_match_share": round(float(frame["region_match_share"].mean()), 4),
        "avg_mood_match_share": round(float(frame["mood_match_share"].mean()), 4),
        "avg_preview_share": round(float(frame["preview_share"].mean()), 4),
        "avg_top_hybrid_score": round(float(frame["top_hybrid_score"].mean()), 4),
        "avg_top_visual_score": round(float(frame["top_visual_score"].mean()), 4),
    }


def compare_engines(
    *,
    df: pd.DataFrame,
    texts: list[str],
    cases: list[dict[str, Any]],
    siglip_model: str,
    output_dir: Path,
    batch_size: int,
    candidate_count: int,
    top_k: int,
    force_siglip: bool,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    clip_spec = EngineSpec(
        name="clip",
        model_name="openai/clip-vit-base-patch32",
        embeddings_path=Path(EMBEDDINGS_PATH),
        manifest_path=Path(f"{EMBEDDINGS_PATH}.manifest.json"),
        kind="clip",
    )
    siglip_slug = siglip_model.replace("/", "__")
    siglip_spec = EngineSpec(
        name="siglip",
        model_name=siglip_model,
        embeddings_path=output_dir / f"song_embeddings_{siglip_slug}_fp16.npy",
        manifest_path=output_dir / f"song_embeddings_{siglip_slug}_fp16.npy.manifest.json",
        kind="siglip",
    )

    full_clip_embeddings = np.load(clip_spec.embeddings_path, allow_pickle=False)
    if "_source_catalog_index" in df.columns:
        clip_embeddings = full_clip_embeddings[
            df["_source_catalog_index"].astype(int).to_numpy()
        ]
    else:
        clip_embeddings = full_clip_embeddings[: len(df)]
    siglip_embeddings = load_or_build_experiment_embeddings(
        siglip_spec,
        texts=texts,
        batch_size=batch_size,
        force=force_siglip,
    )

    engines = {
        "clip": {
            "spec": clip_spec,
            "index": build_faiss_index(clip_embeddings),
            "queries": encode_texts(
                [_case_prompt(case) for case in cases],
                kind="clip",
                model_name=clip_spec.model_name,
                batch_size=batch_size,
            ),
        },
        "siglip": {
            "spec": siglip_spec,
            "index": build_faiss_index(siglip_embeddings),
            "queries": encode_texts(
                [_case_prompt(case) for case in cases],
                kind="siglip",
                model_name=siglip_spec.model_name,
                batch_size=batch_size,
            ),
        },
    }

    all_case_metrics: list[CaseMetrics] = []
    safe_candidate_count = min(candidate_count, len(df))
    for engine_name, engine in engines.items():
        index = engine["index"]
        if index is None:
            raise RuntimeError(f"Could not build FAISS index for {engine_name}")
        for case_index, case in enumerate(cases):
            all_case_metrics.append(
                _evaluate_case(
                    engine_name=engine_name,
                    query_embedding=engine["queries"][case_index : case_index + 1],
                    index=index,
                    df=df,
                    case=case,
                    candidate_count=safe_candidate_count,
                    top_k=top_k,
                )
            )

    by_engine = {
        engine_name: _aggregate(
            [metric for metric in all_case_metrics if metric.engine == engine_name]
        )
        for engine_name in ("clip", "siglip")
    }
    siglip = by_engine["siglip"]
    clip = by_engine["clip"]
    deltas = {
        key: round(float(siglip[key]) - float(clip[key]), 4)
        for key in siglip
        if key != "cases" and key in clip
    }
    weighted_delta = round(
        (deltas.get("avg_language_match_share", 0.0) * 0.30)
        + (deltas.get("avg_region_match_share", 0.0) * 0.25)
        + (deltas.get("avg_mood_match_share", 0.0) * 0.25)
        + (deltas.get("avg_preview_share", 0.0) * 0.10)
        + (deltas.get("avg_top_hybrid_score", 0.0) * 0.10),
        4,
    )
    recommendation = (
        "siglip_wins_offline" if weighted_delta > 0.02 else
        "clip_wins_or_ties_offline"
    )
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset_rows": int(len(df)),
        "case_count": int(len(cases)),
        "candidate_count": int(safe_candidate_count),
        "top_k": int(top_k),
        "siglip_model": siglip_model,
        "summary": by_engine,
        "deltas_siglip_minus_clip": deltas,
        "weighted_delta": weighted_delta,
        "recommendation": recommendation,
        "case_metrics": [asdict(metric) for metric in all_case_metrics],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=DATASET_PATH)
    parser.add_argument("--golden", default=str(ROOT / "evaluation" / "golden_recommendations.json"))
    parser.add_argument("--siglip-model", default=DEFAULT_SIGLIP_MODEL)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--batch-size", type=int, default=EMBEDDING_BATCH_SIZE)
    parser.add_argument("--candidate-count", type=int, default=50000)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--limit", type=int, default=0, help="Optional quick-test catalog row limit")
    parser.add_argument(
        "--golden-corpus",
        action="store_true",
        help="Use a deterministic relevant subset from golden case filters plus distractors",
    )
    parser.add_argument("--golden-per-case", type=int, default=200)
    parser.add_argument("--golden-distractors", type=int, default=1000)
    parser.add_argument("--force-siglip", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print("Loading and preprocessing catalog...", flush=True)
    df = run_preprocessing(existing_csv=args.dataset, output_path=None)
    if df.empty:
        raise SystemExit("Preprocessing returned an empty catalog.")
    cases = load_golden_cases(args.golden)
    if args.golden_corpus:
        df = build_golden_eval_catalog(
            df,
            cases,
            per_case=args.golden_per_case,
            distractors=args.golden_distractors,
        )
    elif args.limit:
        df = df.head(args.limit).copy()
    texts = df.apply(build_enhanced_description, axis=1).tolist()
    report = compare_engines(
        df=df,
        texts=texts,
        cases=cases,
        siglip_model=args.siglip_model,
        output_dir=Path(args.output_dir),
        batch_size=args.batch_size,
        candidate_count=args.candidate_count,
        top_k=args.top_k,
        force_siglip=args.force_siglip,
    )
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")

    print(json.dumps({
        "summary": report["summary"],
        "deltas_siglip_minus_clip": report["deltas_siglip_minus_clip"],
        "weighted_delta": report["weighted_delta"],
        "recommendation": report["recommendation"],
        "report": str(report_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
