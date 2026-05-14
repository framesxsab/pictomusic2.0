"""Tests for config module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import (
    AUDIO_FEATURE_COLUMNS,
    FEATURE_DESCRIPTORS,
    IMAGE_MOOD_KEYWORDS,
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_UPLOAD_SIZE_BYTES,
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
