"""Tests for config module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import (
    APP_TITLE,
    AUDIO_FEATURE_COLUMNS,
    DEMO_IMAGE_URL,
    FEATURE_DESCRIPTORS,
    IMAGE_MOOD_KEYWORDS,
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_UPLOAD_SIZE_BYTES,
    MOOD_TOP_N,
    PREFERRED_FILTER_MIN_CANDIDATES,
    PREFERRED_PREVIEW_IMPORTANCE_MARGIN,
    RAG_ALPHA_HIGH_CONF,
    RAG_ALPHA_LOW_CONF,
    SCENE_GENRE_MAP,
)


def test_feature_descriptors_have_six_elements():
    """Each descriptor tuple should have 6 elements (col, low, high, low_label, high_label, weight)."""
    for desc in FEATURE_DESCRIPTORS:
        assert len(desc) == 6, f"Descriptor {desc[0]} has {len(desc)} elements, expected 6"


def test_feature_descriptors_cover_audio_columns():
    """All audio feature columns should have a corresponding descriptor."""
    descriptor_cols = {d[0] for d in FEATURE_DESCRIPTORS}
    for col in AUDIO_FEATURE_COLUMNS:
        assert col in descriptor_cols, f"Missing descriptor for {col}"


def test_feature_descriptors_thresholds_valid():
    """Low threshold should be less than high threshold."""
    for col, low, high, _, _, _ in FEATURE_DESCRIPTORS:
        assert low < high, f"{col}: low_thresh ({low}) >= high_thresh ({high})"


def test_feature_descriptors_weights_positive():
    """All weights should be positive."""
    for col, _, _, _, _, weight in FEATURE_DESCRIPTORS:
        assert weight > 0, f"{col}: weight ({weight}) is not positive"


def test_mood_keywords_not_empty():
    """Each mood category should have at least one keyword."""
    for mood, keywords in IMAGE_MOOD_KEYWORDS.items():
        assert len(keywords) > 0, f"Mood '{mood}' has no keywords"


def test_allowed_extensions():
    assert ".jpg" in ALLOWED_IMAGE_EXTENSIONS
    assert ".png" in ALLOWED_IMAGE_EXTENSIONS
    assert ".webp" in ALLOWED_IMAGE_EXTENSIONS


def test_upload_size_limit():
    assert MAX_UPLOAD_SIZE_BYTES == 10 * 1024 * 1024


def test_preferred_filter_candidate_floor_supports_preview_availability():
    assert PREFERRED_FILTER_MIN_CANDIDATES >= 50000


def test_preferred_preview_margin_is_stronger_than_generic_margin():
    assert PREFERRED_PREVIEW_IMPORTANCE_MARGIN >= 0.25


def test_scene_genre_map_keys_are_mood_categories():
    """Every scene→genre map key must be a valid IMAGE_MOOD_KEYWORDS category."""
    for scene in SCENE_GENRE_MAP:
        assert scene in IMAGE_MOOD_KEYWORDS, f"SCENE_GENRE_MAP key '{scene}' not in IMAGE_MOOD_KEYWORDS"


def test_scene_genre_map_values_non_empty():
    for scene, genres in SCENE_GENRE_MAP.items():
        assert len(genres) > 0, f"SCENE_GENRE_MAP['{scene}'] has no genres"


def test_rag_alpha_high_conf_is_lower_than_low_conf():
    """High confidence should give more weight to text (lower alpha = less image)."""
    assert RAG_ALPHA_HIGH_CONF < RAG_ALPHA_LOW_CONF


def test_mood_top_n_is_at_least_two():
    assert MOOD_TOP_N >= 2


def test_app_title_uses_public_brand_name():
    assert APP_TITLE == "PictoMusic 2.0"


def test_demo_image_url_is_real_https_url():
    assert DEMO_IMAGE_URL.startswith("https://")
    assert "example.com" not in DEMO_IMAGE_URL
