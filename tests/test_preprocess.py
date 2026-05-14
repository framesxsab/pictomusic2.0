"""Tests for preprocessing pipeline."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from preprocess import (
    build_enhanced_description,
    infer_mood_tags,
    infer_tags_from_source,
    load_dataset,
    validate_and_clean,
)


class TestLoadDataset:
    def test_loads_csv(self, temp_csv):
        df = load_dataset(temp_csv)
        assert len(df) == 50
        assert "name" in df.columns
        assert "artist" in df.columns


class TestInferTagsFromSource:
    def test_tags_bollywood(self):
        df = pd.DataFrame({"source": ["bollywood_2024"], "name": ["test"], "artist": ["test"]})
        result = infer_tags_from_source(df)
        assert result["language"].iloc[0] == "hi"
        assert result["genre"].iloc[0] == "bollywood"
        assert result["region"].iloc[0] == "bollywood"

    def test_tags_regional_tamil(self):
        df = pd.DataFrame({"source": ["regional_Tamil"], "name": ["test"], "artist": ["test"]})
        result = infer_tags_from_source(df)
        assert result["language"].iloc[0] == "ta"
        assert result["genre"].iloc[0] == "tamil"
        assert result["region"].iloc[0] == "south_indian"

    def test_tags_original_western(self):
        df = pd.DataFrame({"source": ["original"], "name": ["test"], "artist": ["test"]})
        result = infer_tags_from_source(df)
        assert result["language"].iloc[0] == "en"
        assert result["region"].iloc[0] == "western"

    def test_tags_unknown_source_defaults_to_western(self):
        df = pd.DataFrame({"source": ["unknown_source"], "name": ["test"], "artist": ["test"]})
        result = infer_tags_from_source(df)
        assert result["language"].iloc[0] == "en"
        assert result["region"].iloc[0] == "western"

    def test_no_source_column(self):
        df = pd.DataFrame({"name": ["test"], "artist": ["test"]})
        result = infer_tags_from_source(df)
        assert "language" in result.columns
        assert result["language"].iloc[0] == "en"

    def test_tags_regional_punjabi(self):
        df = pd.DataFrame({"source": ["regional_Punjabi"], "name": ["test"], "artist": ["test"]})
        result = infer_tags_from_source(df)
        assert result["language"].iloc[0] == "pa"
        assert result["genre"].iloc[0] == "punjabi"

    def test_all_source_types_mapped(self):
        """All known source values should produce valid tags."""
        from preprocess import SOURCE_TAG_MAP
        for source, (lang, genre, region) in SOURCE_TAG_MAP.items():
            assert lang, f"Empty language for source: {source}"
            assert genre, f"Empty genre for source: {source}"
            assert region, f"Empty region for source: {source}"


class TestInferMoodTags:
    def test_energetic_happy(self):
        row = pd.Series({"valence": 0.8, "energy": 0.8, "danceability": 0.8,
                         "acousticness": 0.1, "instrumentalness": 0.0, "genre": "pop"})
        tags = infer_mood_tags(row)
        assert "energetic" in tags
        assert "happy" in tags

    def test_sad_melancholic(self):
        row = pd.Series({"valence": 0.15, "energy": 0.2, "danceability": 0.3,
                         "acousticness": 0.8, "instrumentalness": 0.0, "genre": "ballad"})
        tags = infer_mood_tags(row)
        assert "melancholic" in tags

    def test_calm_peaceful(self):
        row = pd.Series({"valence": 0.4, "energy": 0.2, "danceability": 0.3,
                         "acousticness": 0.8, "instrumentalness": 0.0, "genre": "ambient"})
        tags = infer_mood_tags(row)
        assert "calm" in tags
        assert "peaceful" in tags

    def test_devotional_genre(self):
        row = pd.Series({"valence": 0.4, "energy": 0.3, "danceability": 0.3,
                         "acousticness": 0.8, "instrumentalness": 0.2, "genre": "devotional"})
        tags = infer_mood_tags(row)
        assert "devotional" in tags

    def test_handles_nan_values(self):
        row = pd.Series({"valence": np.nan, "energy": 0.5, "danceability": 0.5,
                         "acousticness": 0.5, "instrumentalness": np.nan, "genre": "pop"})
        tags = infer_mood_tags(row)
        assert isinstance(tags, str)

    def test_handles_missing_keys(self):
        """With missing keys, defaults kick in — should not crash."""
        row = pd.Series({"valence": None, "energy": 0.5})
        tags = infer_mood_tags(row)
        assert isinstance(tags, str)  # Should not crash


class TestValidateAndClean:
    def test_removes_empty_rows(self):
        df = pd.DataFrame({
            "name": ["Song1", "", "Song3"],
            "artist": ["Artist1", "", "Artist3"],
            "danceability": [0.5, 0.5, 0.5],
            "energy": [0.5, 0.5, 0.5],
            "valence": [0.5, 0.5, 0.5],
            "acousticness": [0.5, 0.5, 0.5],
            "instrumentalness": [0.0, 0.0, 0.0],
            "liveness": [0.1, 0.1, 0.1],
            "speechiness": [0.05, 0.05, 0.05],
        })
        cleaned = validate_and_clean(df)
        assert len(cleaned) == 2

    def test_removes_nan_string_rows(self):
        df = pd.DataFrame({
            "name": ["Song1", "nan", "Song3"],
            "artist": ["Artist1", "nan", "Artist3"],
            "danceability": [0.5, 0.5, 0.5],
            "energy": [0.5, 0.5, 0.5],
            "valence": [0.5, 0.5, 0.5],
            "acousticness": [0.5, 0.5, 0.5],
            "instrumentalness": [0.0, 0.0, 0.0],
            "liveness": [0.1, 0.1, 0.1],
            "speechiness": [0.05, 0.05, 0.05],
        })
        cleaned = validate_and_clean(df)
        assert len(cleaned) == 2

    def test_clips_features(self):
        df = pd.DataFrame({
            "name": ["Song1"],
            "artist": ["Artist1"],
            "danceability": [1.5],
            "energy": [-0.3],
            "valence": [0.5],
            "acousticness": [0.5],
            "instrumentalness": [0.0],
            "liveness": [0.1],
            "speechiness": [0.05],
        })
        cleaned = validate_and_clean(df)
        assert cleaned["danceability"].iloc[0] == 1.0
        assert cleaned["energy"].iloc[0] == 0.0

    def test_fills_nan_instrumentalness(self):
        """NaN instrumentalness should be filled with median."""
        df = pd.DataFrame({
            "name": ["Song1", "Song2", "Song3"],
            "artist": ["A1", "A2", "A3"],
            "danceability": [0.5, 0.5, 0.5],
            "energy": [0.5, 0.5, 0.5],
            "valence": [0.5, 0.5, 0.5],
            "acousticness": [0.5, 0.5, 0.5],
            "instrumentalness": [0.2, np.nan, 0.4],
            "liveness": [0.1, 0.1, 0.1],
            "speechiness": [0.05, 0.05, 0.05],
        })
        cleaned = validate_and_clean(df)
        assert not pd.isna(cleaned["instrumentalness"].iloc[1])


class TestBuildEnhancedDescription:
    def test_basic_bollywood_description(self):
        row = pd.Series({
            "name": "Tum Hi Ho", "artist": "Arijit Singh",
            "genre": "bollywood", "language": "hi",
            "energy": 0.55, "valence": 0.25, "danceability": 0.45,
            "acousticness": 0.65, "instrumentalness": 0.0,
            "speechiness": 0.03, "liveness": 0.12,
            "mood_tags": "melancholic,romantic",
        })
        desc = build_enhanced_description(row)
        assert "Tum Hi Ho" in desc
        assert "Arijit Singh" in desc
        assert "bollywood" in desc
        assert "hindi" in desc

    def test_english_song_no_language_tag(self):
        row = pd.Series({
            "name": "Test Song", "artist": "Test Artist",
            "genre": "pop", "language": "en",
            "energy": 0.5, "valence": 0.5, "danceability": 0.5,
            "acousticness": 0.5, "instrumentalness": 0.0,
            "speechiness": 0.03, "liveness": 0.12,
            "mood_tags": "",
        })
        desc = build_enhanced_description(row)
        # English shouldn't be tagged, and "pop" is filtered out
        assert "english" not in desc.lower()

    def test_unknown_song(self):
        row = pd.Series({
            "name": "", "artist": "",
            "genre": "", "language": "",
            "energy": 0.5, "valence": 0.5, "danceability": 0.5,
            "acousticness": 0.5, "instrumentalness": 0.0,
            "speechiness": 0.03, "liveness": 0.12,
            "mood_tags": "",
        })
        desc = build_enhanced_description(row)
        assert desc == "unknown song"

    def test_high_energy_descriptor(self):
        row = pd.Series({
            "name": "Dance", "artist": "DJ",
            "genre": "pop", "language": "en",
            "energy": 0.9, "valence": 0.9, "danceability": 0.9,
            "acousticness": 0.1, "instrumentalness": 0.0,
            "speechiness": 0.03, "liveness": 0.12,
            "mood_tags": "",
        })
        desc = build_enhanced_description(row)
        assert "energetic" in desc
        assert "danceable" in desc

    def test_tamil_song(self):
        row = pd.Series({
            "name": "Vaathi Coming", "artist": "Anirudh",
            "genre": "tamil", "language": "ta",
            "energy": 0.9, "valence": 0.85, "danceability": 0.88,
            "acousticness": 0.05, "instrumentalness": 0.0,
            "speechiness": 0.08, "liveness": 0.22,
            "mood_tags": "energetic,danceable",
        })
        desc = build_enhanced_description(row)
        assert "tamil" in desc.lower()
        assert "Anirudh" in desc

    def test_punjabi_song(self):
        row = pd.Series({
            "name": "Excuses", "artist": "AP Dhillon",
            "genre": "punjabi", "language": "pa",
            "energy": 0.7, "valence": 0.55, "danceability": 0.75,
            "acousticness": 0.12, "instrumentalness": 0.0,
            "speechiness": 0.05, "liveness": 0.10,
            "mood_tags": "",
        })
        desc = build_enhanced_description(row)
        assert "punjabi" in desc.lower()
