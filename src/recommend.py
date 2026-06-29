"""
PictoMusic Recommendation Engine
Image-to-music recommendation using CLIP embeddings, FAISS search, and mood re-ranking.
"""

import logging
import os
import io
from pathlib import Path
from typing import Any, Callable, List, Optional

import numpy as np
import pandas as pd
import requests
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from config import (
    CLIP_MODEL_NAME,
    DEFAULT_TOP_K,
    DATASET_PATH,
    EMBEDDINGS_MANIFEST_PATH,
    EMBEDDINGS_PATH,
    HTTP_CHUNK_SIZE,
    IMAGE_MOOD_KEYWORDS,
    MAX_IMAGE_PIXELS,
    MAX_TOKEN_LENGTH,
    MAX_UPLOAD_SIZE_BYTES,
    METADATA_BACKFILL_LIMIT,
    METADATA_BACKFILL_SCORE_PERCENTILE,
    MOOD_CONFIDENCE_THRESHOLD,
    MOOD_FETCH_MULTIPLIER,
    MOOD_RERANK_BOOST,
    MOOD_SIMILARITY_THRESHOLD,
    MOOD_TOP_N,
    PREFERRED_FILTER_MIN_CANDIDATES,
    PREFERRED_PREVIEW_IMPORTANCE_MARGIN,
    RAG_ALPHA,
    RAG_ALPHA_HIGH_CONF,
    RAG_ALPHA_LOW_CONF,
    REQUEST_TIMEOUT,
    RETRIEVAL_CANDIDATE_MULTIPLIER,
    SCENE_GENRE_BOOST,
    SCENE_GENRE_MAP,
    STRICT_EMBEDDING_MANIFEST,
)
from embeddings import (
    build_faiss_index,
    generate_image_embedding,
    generate_text_embeddings,
    load_or_generate_embeddings,
)
from image_context import analyze_image_context
from preprocess import build_enhanced_description, run_preprocessing
from ranking import (
    apply_hybrid_ranking,
    apply_visual_intent_guardrails,
    deduplicate_recommendations,
    diversify_recommendations,
    prioritize_preference_matches,
    promote_preview_recommendations,
)
from security import validate_image_content, validate_image_url

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

logger = logging.getLogger(__name__)


class ImageMusicRecommender:
    """Image-to-music recommendation system using CLIP embeddings, FAISS, and mood re-ranking."""

    def __init__(
        self,
        clip_model_name: str = CLIP_MODEL_NAME,
        embeddings_path: Optional[str] = None,
        dataset_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ):
        self.clip_model_name = clip_model_name
        self.embeddings_path = embeddings_path or EMBEDDINGS_PATH
        self.dataset_path = dataset_path or DATASET_PATH
        self.embeddings_manifest_path = (
            EMBEDDINGS_MANIFEST_PATH
            if self.embeddings_path == EMBEDDINGS_PATH
            else f"{self.embeddings_path}.manifest.json"
        )

        self.clip_model: Optional[CLIPModel] = None
        self.processor: Optional[CLIPProcessor] = None
        self.music_df: Optional[pd.DataFrame] = None
        self.song_embeddings: Optional[np.ndarray] = None
        self.index: Optional[Any] = None
        self.mood_text_embeddings: Optional[np.ndarray] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.last_detected_themes: List[str] = []
        self.last_mood_confidence: float = 0.0
        self.last_query_text: str = ""
        self.last_candidate_count: int = 0
        self.last_image_context: dict = {}
        self.last_backfill_count: int = 0

        self._load_models()
        self._load_dataset()
        self._load_or_generate_embeddings(progress_callback=progress_callback)
        self._build_faiss_index()
        self._prepare_mood_embeddings()

    def _load_models(self) -> None:
        """Load CLIP model and processor."""
        try:
            self.clip_model = CLIPModel.from_pretrained(
                self.clip_model_name
            ).to(self.device)
            self.processor = CLIPProcessor.from_pretrained(self.clip_model_name)
            self.clip_model.eval()
            logger.info("CLIP model loaded on %s", self.device)
        except Exception as e:
            logger.error("Error loading CLIP model: %s", e, exc_info=True)
            self.clip_model = None
            self.processor = None

    def _load_dataset(self) -> None:
        """Load and preprocess the music dataset (merges Indian songs)."""
        try:
            self.music_df = run_preprocessing(
                existing_csv=self.dataset_path,
                output_path=None,
            )
            logger.info("Dataset loaded: %d songs", len(self.music_df))
        except Exception as e:
            logger.error("Error loading dataset: %s", e, exc_info=True)
            self.music_df = None

    def _load_or_generate_embeddings(self, progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """Load cached embeddings or generate from dataset."""
        if self.music_df is None:
            return

        texts = self.music_df.apply(build_enhanced_description, axis=1).tolist()
        self.song_embeddings = load_or_generate_embeddings(
            dataset_size=len(self.music_df),
            embeddings_path=self.embeddings_path,
            texts=texts,
            model=self.clip_model,
            processor=self.processor,
            device=self.device,
            model_name=self.clip_model_name,
            manifest_path=self.embeddings_manifest_path,
            strict_manifest=STRICT_EMBEDDING_MANIFEST,
            progress_callback=progress_callback,
        )

    def _build_faiss_index(self) -> None:
        """Build FAISS similarity search index."""
        if self.song_embeddings is None:
            return
        self.index = build_faiss_index(self.song_embeddings)

    @torch.no_grad()
    def _prepare_mood_embeddings(self) -> None:
        """Pre-compute CLIP text embeddings for mood classification prompts."""
        if self.clip_model is None or self.processor is None:
            return

        try:
            mood_texts = [f"a photo of {mood}" for mood in IMAGE_MOOD_KEYWORDS.keys()]
            self.mood_text_embeddings = generate_text_embeddings(
                mood_texts, self.clip_model, self.processor, self.device,
                batch_size=len(mood_texts),
            )
            logger.info("Mood classification embeddings prepared (%d categories)", len(mood_texts))
        except Exception as e:
            logger.warning("Could not prepare mood embeddings: %s", e)
            self.mood_text_embeddings = None

    def _classify_image_mood(self, image_embedding: np.ndarray) -> List[str]:
        """Zero-shot classify image mood using CLIP text-image similarity.
        Returns top mood keywords and caches confidence score for adaptive RAG blending.
        Higher confidence = the image is a clear match for specific scenes.
        """
        if self.mood_text_embeddings is None:
            return []

        try:
            similarities = np.dot(
                self.mood_text_embeddings.astype("float32"),
                image_embedding.astype("float32").T,
            ).flatten()

            mood_keys = list(IMAGE_MOOD_KEYWORDS.keys())
            top_indices = similarities.argsort()[-MOOD_TOP_N:][::-1]
            top_moods = [
                mood_keys[i] for i in top_indices
                if similarities[i] > MOOD_SIMILARITY_THRESHOLD
            ]

            # Compute mood confidence: average similarity of accepted moods.
            # This drives adaptive RAG blending — high confidence = lean more on text query.
            if top_moods:
                accepted_sims = [float(similarities[i]) for i in top_indices
                                 if similarities[i] > MOOD_SIMILARITY_THRESHOLD]
                self.last_mood_confidence = float(np.mean(accepted_sims))
            else:
                self.last_mood_confidence = 0.0

            self.last_detected_themes = top_moods

            mood_keywords = []
            seen_keywords = set()
            for mood in top_moods:
                for keyword in IMAGE_MOOD_KEYWORDS[mood]:
                    normalized_keyword = keyword.lower()
                    if normalized_keyword not in seen_keywords:
                        mood_keywords.append(keyword)
                        seen_keywords.add(normalized_keyword)

            return mood_keywords
        except Exception as e:
            logger.warning("Mood classification failed: %s", e)
            self.last_mood_confidence = 0.0
            return []

    def _build_visual_music_query(self, mood_keywords: List[str]) -> str:
        """Build a deterministic CLIP text query from detected visual context."""
        query_parts = []

        if self.last_detected_themes:
            query_parts.append(
                "visual scene: " + ", ".join(self.last_detected_themes[:MOOD_TOP_N])
            )

        if mood_keywords:
            query_parts.append("music mood: " + ", ".join(mood_keywords[:8]))

        image_context = getattr(self, "last_image_context", {}) or {}
        context_labels = image_context.get("labels", [])
        context_cues = image_context.get("music_cues", [])
        if context_labels:
            query_parts.append("image tone: " + ", ".join(context_labels[:5]))
        if context_cues:
            query_parts.append("tone cues: " + ", ".join(context_cues[:8]))

        preferred_genres = []
        seen_genres = set()
        for theme in self.last_detected_themes:
            for genre in SCENE_GENRE_MAP.get(theme, []):
                clean_genre = genre.replace("_", " ").strip()
                if clean_genre and clean_genre not in seen_genres:
                    preferred_genres.append(clean_genre)
                    seen_genres.add(clean_genre)
        if preferred_genres:
            query_parts.append("preferred styles: " + ", ".join(preferred_genres[:6]))

        return ". ".join(query_parts) if query_parts else "music matching the image"

    def _rerank_with_mood(
        self, results: pd.DataFrame, mood_keywords: List[str]
    ) -> pd.DataFrame:
        """Boost similarity scores for songs whose mood_tags match detected image mood."""
        if not mood_keywords or "mood_tags" not in results.columns or "similarity_score" not in results.columns:
            return results

        results = results.copy()
        mood_set = set(k.lower() for k in mood_keywords)

        def compute_boost(row):
            tags = str(row.get("mood_tags", "")).lower().split(",")
            overlap = sum(1 for t in tags if t.strip() in mood_set)
            return overlap * MOOD_RERANK_BOOST

        results["_mood_boost"] = results.apply(compute_boost, axis=1)
        results["similarity_score"] = results["similarity_score"] + results["_mood_boost"]
        results.drop(columns="_mood_boost", inplace=True)
        results.sort_values("similarity_score", ascending=False, inplace=True)
        results.reset_index(drop=True, inplace=True)

        return results

    def _rerank_with_scene_genre(
        self, results: pd.DataFrame, detected_themes: List[str]
    ) -> pd.DataFrame:
        """Boost songs whose genre matches the detected visual scene.
        E.g., a temple image boosts devotional/classical songs.
        """
        if not detected_themes or "genre" not in results.columns or "similarity_score" not in results.columns:
            return results

        # Collect all preferred genres from detected scenes
        preferred_genres = set()
        for theme in detected_themes:
            for genre in SCENE_GENRE_MAP.get(theme, []):
                preferred_genres.add(genre.lower())

        if not preferred_genres:
            return results

        results = results.copy()
        genre_match = results["genre"].fillna("").astype(str).str.lower().isin(preferred_genres).astype(float)
        results["similarity_score"] = results["similarity_score"] + genre_match * SCENE_GENRE_BOOST
        results.sort_values("similarity_score", ascending=False, inplace=True)
        results.reset_index(drop=True, inplace=True)
        return results

    def _metadata_backfill_candidates(
        self,
        existing_indices: set,
        *,
        mood_keywords: List[str],
        preferred_language: str,
        preferred_region: str,
        score_floor: float,
    ) -> pd.DataFrame:
        """Add structured candidates when vector retrieval misses obvious intent matches."""
        if self.music_df is None or METADATA_BACKFILL_LIMIT <= 0:
            return pd.DataFrame()

        preferred_language = str(preferred_language or "any").strip().lower()
        preferred_region = str(preferred_region or "any").strip().lower()
        mood_set = {str(mood).strip().lower() for mood in mood_keywords if str(mood).strip()}
        has_language_pref = preferred_language != "any"
        has_region_pref = preferred_region != "any"
        if not has_language_pref and not has_region_pref and not mood_set:
            return pd.DataFrame()

        df = self.music_df
        mask = pd.Series(True, index=df.index)
        if has_language_pref and "language" in df.columns:
            mask &= df["language"].fillna("").astype(str).str.lower().eq(preferred_language)
        if has_region_pref and "region" in df.columns:
            mask &= df["region"].fillna("").astype(str).str.lower().eq(preferred_region)
        if mood_set and "mood_tags" in df.columns:
            mask &= df["mood_tags"].fillna("").astype(str).str.lower().map(
                lambda value: bool({tag.strip() for tag in value.split(",")} & mood_set)
            )
        if existing_indices:
            mask &= ~df.index.isin(existing_indices)

        backfill = df[mask].copy()
        if backfill.empty:
            return backfill

        backfill["_has_preview"] = (
            backfill["preview"].astype(str).str.startswith("http")
            if "preview" in backfill.columns
            else False
        )
        backfill["_catalog_year"] = pd.to_numeric(
            backfill.get("catalog_year", 0), errors="coerce"
        ).fillna(0)
        backfill["_popularity"] = pd.to_numeric(
            backfill.get("popularity", 0), errors="coerce"
        ).fillna(0)
        backfill.sort_values(
            ["_has_preview", "_catalog_year", "_popularity"],
            ascending=[False, False, False],
            inplace=True,
        )
        backfill = backfill.head(METADATA_BACKFILL_LIMIT).copy()
        backfill["visual_score"] = float(score_floor)
        backfill["similarity_score"] = float(score_floor)
        backfill["_retrieval_source"] = "metadata_backfill"
        return backfill.drop(
            columns=["_has_preview", "_catalog_year", "_popularity"],
            errors="ignore",
        )

    @property
    def is_ready(self) -> bool:
        return all([
            self.music_df is not None,
            self.index is not None,
            self.clip_model is not None,
            self.processor is not None,
        ])

    def missing_components(self) -> List[str]:
        missing = []
        if self.music_df is None:
            missing.append("Dataset (Music.csv)")
        if self.index is None:
            missing.append("Embeddings / FAISS index")
        if self.clip_model is None or self.processor is None:
            missing.append("CLIP Model / Processor")
        return missing

    def catalog_stats(self) -> dict:
        """Return user-facing catalog health metrics."""
        if self.music_df is None or self.music_df.empty:
            return {"songs": 0, "india_pct": 0.0, "preview_pct": 0.0, "languages": 0}

        df = self.music_df
        india_pct = 0.0
        if "india_affinity" in df.columns:
            india_pct = float((df["india_affinity"].fillna(0) > 0).mean() * 100)

        preview_pct = 0.0
        if "preview" in df.columns:
            preview_pct = float(df["preview"].astype(str).str.startswith("http").mean() * 100)

        languages = int(df["language"].nunique()) if "language" in df.columns else 0
        return {
            "songs": int(len(df)),
            "india_pct": india_pct,
            "preview_pct": preview_pct,
            "languages": languages,
        }

    def _get_image_embedding(self, image_source) -> Optional[np.ndarray]:
        """Process various image sources into a CLIP embedding."""
        if self.clip_model is None or self.processor is None:
            return None

        try:
            if isinstance(image_source, Image.Image):
                image = image_source.convert("RGB")

            elif hasattr(image_source, "getvalue"):
                image_bytes = image_source.getvalue()
                validate_image_content(image_bytes)
                image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

            elif isinstance(image_source, str) and image_source.startswith("http"):
                validated_url = validate_image_url(image_source)
                response = requests.get(
                    validated_url, stream=True, timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()

                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_UPLOAD_SIZE_BYTES:
                    raise ValueError(
                        f"Remote image too large ({int(content_length)} bytes)"
                    )

                downloaded = []
                downloaded_size = 0
                for chunk in response.iter_content(chunk_size=HTTP_CHUNK_SIZE):
                    downloaded_size += len(chunk)
                    if downloaded_size > MAX_UPLOAD_SIZE_BYTES:
                        raise ValueError(
                            "Remote image exceeds size limit during download"
                        )
                    downloaded.append(chunk)

                image_bytes = b"".join(downloaded)
                validate_image_content(image_bytes)
                image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

            else:
                image = Image.open(str(image_source)).convert("RGB")

            context = analyze_image_context(image)
            self.last_image_context = {
                "labels": context.labels,
                "music_cues": context.music_cues,
                "metrics": context.metrics,
            }

            return generate_image_embedding(
                image, self.clip_model, self.processor, self.device
            )

        except ValueError as ve:
            logger.warning("Image validation failed: %s", ve)
            return None
        except requests.RequestException as re:
            logger.error("HTTP error fetching image: %s", re)
            return None
        except (OSError, IOError) as ie:
            logger.error("Image file error: %s", ie)
            return None
        except Exception as e:
            logger.error("Error processing image: %s", e, exc_info=True)
            return None

    def recommend(
        self,
        image_source,
        top_k: int = DEFAULT_TOP_K,
        show_scores: bool = True,
        preferred_language: str = "any",
        preferred_region: str = "any",
        prefer_recent: bool = True,
        require_preview: bool = False,
        boost_indian: bool = False,
    ) -> pd.DataFrame:
        """Get music recommendations for an image.
        Returns a DataFrame with song info and similarity scores.
        """
        if not self.is_ready:
            logger.error("Recommender not fully initialized.")
            return pd.DataFrame()

        self.last_detected_themes = []  # Reset on each call
        self.last_mood_confidence = 0.0
        self.last_query_text = ""
        self.last_candidate_count = 0
        self.last_image_context = {}
        self.last_backfill_count = 0

        img_emb = self._get_image_embedding(image_source)
        if img_emb is None:
            logger.error("Failed to process image.")
            return pd.DataFrame()

        try:
            # 1. Zero-shot classify image into scene categories and mood keywords
            mood_keywords = self._classify_image_mood(img_emb)

            # 2. Build a deterministic text query that bridges visual scenes to music labels.
            query_text = self._build_visual_music_query(mood_keywords)
            self.last_query_text = query_text

            # Generate CLIP text embedding for the constructed query
            query_text_emb = generate_text_embeddings(
                [query_text],
                self.clip_model,
                self.processor,
                self.device,
                batch_size=1,
            )

            # 3. Confidence-adaptive RAG blending.
            # High mood confidence → trust text query more (lower alpha).
            # Low confidence → lean on raw image embedding (higher alpha).
            if query_text_emb is not None and self.last_mood_confidence > 0:
                if self.last_mood_confidence >= MOOD_CONFIDENCE_THRESHOLD:
                    alpha = RAG_ALPHA_HIGH_CONF
                else:
                    alpha = RAG_ALPHA_LOW_CONF
                blended_emb = alpha * img_emb + (1.0 - alpha) * query_text_emb
                blended_norm = np.linalg.norm(blended_emb, axis=-1, keepdims=True)
                blended_emb = blended_emb / np.where(blended_norm > 0, blended_norm, 1.0)
                logger.info("RAG blend: alpha=%.2f, mood_conf=%.3f, query=%r",
                            alpha, self.last_mood_confidence, query_text[:80])
            else:
                blended_emb = img_emb

            # Fetch more candidates using the blended RAG embedding
            candidate_multiplier = max(MOOD_FETCH_MULTIPLIER, RETRIEVAL_CANDIDATE_MULTIPLIER)
            min_candidates = top_k * candidate_multiplier
            if preferred_language != "any" or preferred_region != "any":
                min_candidates = max(min_candidates, PREFERRED_FILTER_MIN_CANDIDATES)
            fetch_k = min(min_candidates, self.index.ntotal)
            self.last_candidate_count = int(fetch_k)
            distances, indices = self.index.search(blended_emb.astype("float32"), fetch_k)
            results = self.music_df.iloc[indices[0]].copy()

            raw_scores = distances[0].astype(float)
            results["visual_score"] = raw_scores
            results["similarity_score"] = raw_scores
            results["_retrieval_source"] = "clip"

            score_floor = float(np.percentile(raw_scores, METADATA_BACKFILL_SCORE_PERCENTILE))
            backfill = self._metadata_backfill_candidates(
                set(results.index),
                mood_keywords=mood_keywords,
                preferred_language=preferred_language,
                preferred_region=preferred_region,
                score_floor=score_floor,
            )
            self.last_backfill_count = int(len(backfill))
            if not backfill.empty:
                results = pd.concat([results, backfill], ignore_index=False)

            # Mood-aware re-ranking
            if mood_keywords:
                results = self._rerank_with_mood(results, mood_keywords)
                logger.info("Re-ranked with mood: %s", mood_keywords[:5])

            # Scene→genre re-ranking
            if self.last_detected_themes:
                results = self._rerank_with_scene_genre(results, self.last_detected_themes)

            results = apply_visual_intent_guardrails(
                results,
                detected_themes=self.last_detected_themes,
                mood_keywords=mood_keywords,
            )

            results = apply_hybrid_ranking(
                results,
                preferred_language=preferred_language,
                preferred_region=preferred_region,
                prefer_recent=prefer_recent,
                require_preview=require_preview,
                boost_indian=boost_indian,
            )
            results = deduplicate_recommendations(results)
            results = prioritize_preference_matches(
                results,
                preferred_language=preferred_language,
                preferred_region=preferred_region,
            )
            if not require_preview:
                preferred_language_norm = str(preferred_language or "any").strip().lower()
                preferred_region_norm = str(preferred_region or "any").strip().lower()
                has_language_pref = preferred_language_norm != "any"
                has_region_pref = preferred_region_norm != "any"
                if has_language_pref or has_region_pref:
                    exact_match = pd.Series(True, index=results.index)
                    if has_language_pref and "language" in results.columns:
                        exact_match &= results["language"].fillna("").astype(str).str.lower().eq(
                            preferred_language_norm
                        )
                    if has_region_pref and "region" in results.columns:
                        exact_match &= results["region"].fillna("").astype(str).str.lower().eq(
                            preferred_region_norm
                        )

                    if bool(exact_match.any()):
                        matched = promote_preview_recommendations(
                            results[exact_match],
                            target_size=top_k,
                            importance_margin=PREFERRED_PREVIEW_IMPORTANCE_MARGIN,
                        )
                        results = pd.concat([matched, results[~exact_match]], ignore_index=True)
                    else:
                        results = promote_preview_recommendations(results, target_size=top_k)
                else:
                    results = promote_preview_recommendations(results, target_size=top_k)
            results = prioritize_preference_matches(
                results,
                preferred_language=preferred_language,
                preferred_region=preferred_region,
            )
            results = diversify_recommendations(results, target_size=top_k)

            # Return top_k after re-ranking
            if not show_scores:
                results = results.drop(
                    columns=[
                        "similarity_score",
                        "visual_score",
                        "hybrid_score",
                        "_retrieval_source",
                    ],
                    errors="ignore",
                )
            return results.head(top_k).reset_index(drop=True)

        except Exception as e:
            logger.error("Error during search: %s", e, exc_info=True)
            return pd.DataFrame()
