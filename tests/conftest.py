"""
Shared test fixtures for PictoMusic tests.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture
def sample_music_df():
    """50-row DataFrame with all required columns."""
    np.random.seed(42)
    n = 50
    genres = ["bollywood", "punjabi", "tamil", "pop", "indie", "classical"]
    languages = ["hi", "pa", "ta", "en", "te", "bn"]
    regions = ["bollywood", "punjabi", "south_indian", "western", "indie_indian", "classical_indian"]

    data = {
        "name": [f"Song_{i}" for i in range(n)],
        "artist": [f"Artist_{i % 10}" for i in range(n)],
        "spotify_id": [f"id_{i}" for i in range(n)],
        "preview": [f"https://example.com/preview_{i}.mp3" if i % 3 != 0 else "" for i in range(n)],
        "img": [f"https://example.com/img_{i}.jpg" for i in range(n)],
        "language": [languages[i % len(languages)] for i in range(n)],
        "genre": [genres[i % len(genres)] for i in range(n)],
        "region": [regions[i % len(regions)] for i in range(n)],
        "mood_tags": ["happy,energetic" if i % 2 == 0 else "melancholic,calm" for i in range(n)],
        "danceability": np.random.uniform(0.1, 0.9, n),
        "energy": np.random.uniform(0.1, 0.9, n),
        "valence": np.random.uniform(0.1, 0.9, n),
        "acousticness": np.random.uniform(0.1, 0.9, n),
        "instrumentalness": np.random.uniform(0.0, 0.5, n),
        "liveness": np.random.uniform(0.05, 0.4, n),
        "speechiness": np.random.uniform(0.02, 0.3, n),
        "loudness": np.random.uniform(-15, -3, n),
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_embeddings():
    """Random 50x512 float32 array, L2-normalized."""
    np.random.seed(42)
    emb = np.random.randn(50, 512).astype(np.float32)
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    return emb / norms


@pytest.fixture
def temp_csv(sample_music_df, tmp_path):
    """Write sample_music_df to a temp CSV, return path."""
    path = tmp_path / "test_music.csv"
    sample_music_df.to_csv(str(path), index=False)
    return str(path)


@pytest.fixture
def temp_embeddings(sample_embeddings, tmp_path):
    """Write sample embeddings to a temp .npy, return path."""
    path = tmp_path / "test_embeddings.npy"
    np.save(str(path), sample_embeddings.astype(np.float16))
    return str(path)
