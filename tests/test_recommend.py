"""Tests for recommendation engine."""

import sys
import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

faiss = pytest.importorskip("faiss")
from embeddings import build_faiss_index, normalize_embeddings


class TestBuildFaissIndex:
    def test_normalizes_cached_fp16_vectors_for_cosine_search(self, sample_embeddings):
        scaled = sample_embeddings.astype(np.float16)
        scaled[0] = scaled[0] * 0.25
        normalized = normalize_embeddings(scaled)

        assert np.isclose(np.linalg.norm(normalized[0]), 1.0, atol=1e-6)

    def test_builds_index(self, sample_embeddings):
        index = build_faiss_index(sample_embeddings)
        assert index is not None
        assert index.ntotal == 50

    def test_correct_dimension(self, sample_embeddings):
        index = build_faiss_index(sample_embeddings)
        assert index.d == 512

    def test_search_returns_results(self, sample_embeddings):
        index = build_faiss_index(sample_embeddings)
        query = sample_embeddings[0:1]
        distances, indices = index.search(query, 5)
        assert len(indices[0]) == 5
        assert indices[0][0] == 0  # First result should be the query itself

    def test_scores_are_sorted(self, sample_embeddings):
        index = build_faiss_index(sample_embeddings)
        query = sample_embeddings[0:1]
        distances, indices = index.search(query, 10)
        # Inner product distances should be descending
        for i in range(len(distances[0]) - 1):
            assert distances[0][i] >= distances[0][i + 1]


class TestMoodReranking:
    def test_boost_applied(self):
        """Test that mood re-ranking boosts matching songs."""
        from config import MOOD_RERANK_BOOST

        results = pd.DataFrame({
            "name": ["Song_A", "Song_B", "Song_C"],
            "artist": ["Artist_1", "Artist_2", "Artist_3"],
            "similarity_score": [0.30, 0.29, 0.28],
            "mood_tags": ["sad,calm", "happy,energetic,danceable", "melancholic"],
        })

        mood_keywords = ["happy", "energetic", "danceable"]
        mood_set = set(k.lower() for k in mood_keywords)

        # Apply boost manually (same logic as _rerank_with_mood)
        results_copy = results.copy()
        for idx, row in results_copy.iterrows():
            tags = str(row["mood_tags"]).lower().split(",")
            overlap = sum(1 for t in tags if t.strip() in mood_set)
            results_copy.at[idx, "similarity_score"] += overlap * MOOD_RERANK_BOOST

        results_copy.sort_values("similarity_score", ascending=False, inplace=True)
        # Song_B has 3 matching tags, should be boosted to top
        assert results_copy.iloc[0]["name"] == "Song_B"

    def test_no_boost_when_no_match(self):
        """Songs with no matching mood tags should not be boosted."""
        results = pd.DataFrame({
            "name": ["Song_A"],
            "similarity_score": [0.30],
            "mood_tags": ["sad,calm"],
        })

        mood_keywords = ["happy", "energetic"]
        mood_set = set(k.lower() for k in mood_keywords)

        for idx, row in results.iterrows():
            tags = str(row["mood_tags"]).lower().split(",")
            overlap = sum(1 for t in tags if t.strip() in mood_set)
            assert overlap == 0


class TestVisualQuery:
    def test_visual_music_query_is_ordered_and_genre_aware(self):
        from recommend import ImageMusicRecommender

        recommender = object.__new__(ImageMusicRecommender)
        recommender.last_detected_themes = ["wedding and ceremony", "festival and lights"]
        recommender.last_image_context = {}

        query = recommender._build_visual_music_query(
            ["happy", "romantic", "danceable", "energetic"]
        )

        assert query.startswith("visual scene: wedding and ceremony, festival and lights")
        assert "music mood: happy, romantic, danceable, energetic" in query
        assert "preferred styles: bollywood, punjabi, filmi, folk" in query

    def test_visual_music_query_includes_lightweight_image_context(self):
        from recommend import ImageMusicRecommender

        recommender = object.__new__(ImageMusicRecommender)
        recommender.last_detected_themes = []
        recommender.last_image_context = {
            "labels": ["warm color temperature", "bright lighting"],
            "music_cues": ["warm", "romantic", "upbeat"],
        }

        query = recommender._build_visual_music_query(["happy"])

        assert "image tone: warm color temperature, bright lighting" in query
        assert "tone cues: warm, romantic, upbeat" in query


class TestImageContext:
    def test_analyze_image_context_extracts_warm_bright_cues(self):
        Image = pytest.importorskip("PIL.Image")
        from image_context import analyze_image_context

        image = Image.new("RGB", (64, 64), color=(250, 190, 70))

        context = analyze_image_context(image)

        assert "warm color temperature" in context.labels
        assert "bright lighting" in context.labels
        assert "romantic" in context.music_cues
        assert context.metrics["brightness"] > 0.6


class TestMetadataBackfill:
    def test_metadata_backfill_prefers_preview_matching_intent(self):
        from recommend import ImageMusicRecommender

        recommender = object.__new__(ImageMusicRecommender)
        recommender.music_df = pd.DataFrame(
            {
                "name": ["Existing", "Match Preview", "Match No Preview", "Wrong Mood"],
                "artist": ["A", "B", "C", "D"],
                "language": ["hi", "hi", "hi", "hi"],
                "region": ["bollywood", "bollywood", "bollywood", "bollywood"],
                "mood_tags": ["romantic", "romantic,calm", "romantic", "party"],
                "preview": ["", "https://p/preview.mp3", "", "https://p/wrong.mp3"],
                "catalog_year": [2026, 2026, 2025, 2026],
                "popularity": [90, 80, 95, 100],
            }
        )

        backfill = recommender._metadata_backfill_candidates(
            {0},
            mood_keywords=["romantic"],
            preferred_language="hi",
            preferred_region="bollywood",
            score_floor=0.42,
        )

        assert list(backfill["name"])[:2] == ["Match Preview", "Match No Preview"]
        assert "Existing" not in set(backfill["name"])
        assert "Wrong Mood" not in set(backfill["name"])
        assert backfill.iloc[0]["similarity_score"] == 0.42
        assert backfill.iloc[0]["_retrieval_source"] == "metadata_backfill"


class TestEmbeddingsIO:
    def test_load_cached(self, temp_embeddings):
        from embeddings import load_or_generate_embeddings

        result = load_or_generate_embeddings(
            dataset_size=50,
            embeddings_path=temp_embeddings,
            texts=None,
            model=None,
            processor=None,
            device=None,
        )
        assert result is not None
        assert result.shape[0] == 50

    def test_size_mismatch_without_model(self, temp_embeddings):
        """If size mismatches and no model provided, should return None."""
        from embeddings import load_or_generate_embeddings

        result = load_or_generate_embeddings(
            dataset_size=100,  # Mismatch!
            embeddings_path=temp_embeddings,
            texts=None,
            model=None,
            processor=None,
            device=None,
        )
        assert result is None


def make_uploaded_image(fmt="PNG"):
    Image = pytest.importorskip("PIL.Image")
    image = Image.new("RGB", (16, 16), color=(244, 182, 66))
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    buffer.seek(0)
    buffer.name = f"upload.{fmt.lower()}"
    return buffer


class TestUploadedImageWorkflow:
    def test_uploaded_image_embedding_path_accepts_valid_image(self, monkeypatch):
        from recommend import ImageMusicRecommender

        recommender = object.__new__(ImageMusicRecommender)
        recommender.clip_model = object()
        recommender.processor = object()
        recommender.device = "cpu"

        expected = np.ones((1, 512), dtype=np.float32)
        monkeypatch.setattr("recommend.generate_image_embedding", lambda *args: expected)

        result = recommender._get_image_embedding(make_uploaded_image("PNG"))

        assert result is expected
        assert "labels" in recommender.last_image_context
        assert "music_cues" in recommender.last_image_context

    def test_uploaded_image_embedding_path_rejects_corrupt_image_without_crash(self):
        from recommend import ImageMusicRecommender

        recommender = object.__new__(ImageMusicRecommender)
        recommender.clip_model = object()
        recommender.processor = object()
        recommender.device = "cpu"

        file_obj = io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 100)
        file_obj.name = "upload.jpg"

        assert recommender._get_image_embedding(file_obj) is None
