"""
PictoMusic Recommendation Engine
Image-to-music recommendation using CLIP embeddings, FAISS search, and mood re-ranking.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Callable, List, Optional

import faiss
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
    EMBEDDINGS_PATH,
    HTTP_CHUNK_SIZE,
    IMAGE_MOOD_KEYWORDS,
    MAX_IMAGE_PIXELS,
    MAX_TOKEN_LENGTH,
    MAX_UPLOAD_SIZE_BYTES,
    MOOD_FETCH_MULTIPLIER,
    MOOD_RERANK_BOOST,
    MOOD_SIMILARITY_THRESHOLD,
    MOOD_TOP_N,
    REQUEST_TIMEOUT,
    RETRIEVAL_CANDIDATE_MULTIPLIER,
)
from embeddings import (
    build_faiss_index,
    generate_image_embedding,
    generate_text_embeddings,
    load_or_generate_embeddings,
)
from preprocess import build_enhanced_description, run_preprocessing
from ranking import (
    apply_hybrid_ranking,
    deduplicate_recommendations,
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

        self.clip_model: Optional[CLIPModel] = None
        self.processor: Optional[CLIPProcessor] = None
        self.music_df: Optional[pd.DataFrame] = None
        self.song_embeddings: Optional[np.ndarray] = None
        self.index: Optional[faiss.IndexFlatIP] = None
        self.mood_text_embeddings: Optional[np.ndarray] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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
        Returns top-2 mood keywords that match the image.
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
            top_moods = [mood_keys[i] for i in top_indices if similarities[i] > MOOD_SIMILARITY_THRESHOLD]

            mood_keywords = []
            for mood in top_moods:
                mood_keywords.extend(IMAGE_MOOD_KEYWORDS[mood])

            return list(set(mood_keywords))
        except Exception as e:
            logger.warning("Mood classification failed: %s", e)
            return []

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

        tmp_path: Optional[str] = None
        try:
            if isinstance(image_source, Image.Image):
                image = image_source.convert("RGB")

            elif hasattr(image_source, "getvalue"):
                image_bytes = image_source.getvalue()
                validate_image_content(image_bytes)
                suffix = Path(getattr(image_source, "name", "img.jpg")).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(image_bytes)
                    tmp_path = tmp.name
                image = Image.open(tmp_path).convert("RGB")

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

                downloaded = 0
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    for chunk in response.iter_content(chunk_size=HTTP_CHUNK_SIZE):
                        downloaded += len(chunk)
                        if downloaded > MAX_UPLOAD_SIZE_BYTES:
                            raise ValueError(
                                "Remote image exceeds size limit during download"
                            )
                        tmp.write(chunk)
                    tmp_path = tmp.name
                with open(tmp_path, "rb") as f:
                    validate_image_content(f.read())
                image = Image.open(tmp_path).convert("RGB")

            else:
                image = Image.open(str(image_source)).convert("RGB")

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
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

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

        img_emb = self._get_image_embedding(image_source)
        if img_emb is None:
            logger.error("Failed to process image.")
            return pd.DataFrame()

        try:
            # Fetch more candidates for re-ranking
            candidate_multiplier = max(MOOD_FETCH_MULTIPLIER, RETRIEVAL_CANDIDATE_MULTIPLIER)
            if preferred_language != "any" or preferred_region != "any":
                candidate_multiplier = max(candidate_multiplier, 200)
            fetch_k = min(top_k * candidate_multiplier, self.index.ntotal)
            distances, indices = self.index.search(img_emb.astype("float32"), fetch_k)
            results = self.music_df.iloc[indices[0]].copy()

            if show_scores:
                results["similarity_score"] = distances[0]

            # Mood-aware re-ranking
            mood_keywords = self._classify_image_mood(img_emb)
            if mood_keywords:
                results = self._rerank_with_mood(results, mood_keywords)
                logger.info("Re-ranked with mood: %s", mood_keywords[:5])

            results = apply_hybrid_ranking(
                results,
                preferred_language=preferred_language,
                preferred_region=preferred_region,
                prefer_recent=prefer_recent,
                require_preview=require_preview,
                boost_indian=boost_indian,
            )
            results = deduplicate_recommendations(results)
            if not require_preview:
                results = promote_preview_recommendations(results, target_size=top_k)

            # Return top_k after re-ranking
            return results.head(top_k).reset_index(drop=True)

        except Exception as e:
            logger.error("Error during search: %s", e, exc_info=True)
            return pd.DataFrame()
