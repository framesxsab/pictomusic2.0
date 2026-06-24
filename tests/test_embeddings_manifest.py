"""Tests for embedding cache manifest validation."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from embeddings import (
    build_embeddings_manifest,
    embedding_manifest_matches,
    fingerprint_texts,
    load_or_generate_embeddings,
    read_embeddings_manifest,
    write_embeddings_manifest,
)


def test_fingerprint_texts_changes_when_corpus_changes():
    base = fingerprint_texts(["song one", "song two"])
    changed = fingerprint_texts(["song one", "song two remix"])

    assert base != changed


def test_embedding_manifest_round_trip(tmp_path):
    texts = ["Hindi romantic rain song", "Tamil festival dance song"]
    manifest = build_embeddings_manifest(
        dataset_size=2,
        embedding_shape=(2, 512),
        embedding_dtype="float16",
        model_name="openai/clip-vit-base-patch32",
        text_fingerprint=fingerprint_texts(texts),
    )
    path = tmp_path / "embeddings.npy.manifest.json"

    write_embeddings_manifest(str(path), manifest)

    assert read_embeddings_manifest(str(path)) == manifest


def test_embedding_manifest_detects_model_mismatch():
    texts = ["Punjabi party track"]
    manifest = build_embeddings_manifest(
        dataset_size=1,
        embedding_shape=(1, 512),
        embedding_dtype="float16",
        model_name="openai/clip-vit-base-patch32",
        text_fingerprint=fingerprint_texts(texts),
    )

    matches, reason = embedding_manifest_matches(
        manifest,
        dataset_size=1,
        embedding_shape=(1, 512),
        model_name="local/fine-tuned-pictomusic-clip",
        text_fingerprint=fingerprint_texts(texts),
    )

    assert not matches
    assert "model_name mismatch" in reason


def test_embedding_manifest_detects_dtype_mismatch():
    texts = ["Punjabi party track"]
    manifest = build_embeddings_manifest(
        dataset_size=1,
        embedding_shape=(1, 512),
        embedding_dtype="float16",
        model_name="openai/clip-vit-base-patch32",
        text_fingerprint=fingerprint_texts(texts),
    )

    matches, reason = embedding_manifest_matches(
        manifest,
        dataset_size=1,
        embedding_shape=(1, 512),
        embedding_dtype="float32",
        model_name="openai/clip-vit-base-patch32",
        text_fingerprint=fingerprint_texts(texts),
    )

    assert not matches
    assert "embedding_dtype mismatch" in reason


def test_load_cached_embeddings_with_verified_manifest(sample_embeddings, tmp_path):
    texts = [f"song {i}" for i in range(len(sample_embeddings))]
    embeddings_path = tmp_path / "embeddings.npy"
    manifest_path = tmp_path / "embeddings.npy.manifest.json"
    np.save(str(embeddings_path), sample_embeddings.astype(np.float16))
    manifest = build_embeddings_manifest(
        dataset_size=len(sample_embeddings),
        embedding_shape=tuple(sample_embeddings.shape),
        embedding_dtype="float16",
        model_name="openai/clip-vit-base-patch32",
        text_fingerprint=fingerprint_texts(texts),
    )
    write_embeddings_manifest(str(manifest_path), manifest)

    loaded = load_or_generate_embeddings(
        dataset_size=len(sample_embeddings),
        embeddings_path=str(embeddings_path),
        texts=texts,
        model=None,
        processor=None,
        device=None,
        model_name="openai/clip-vit-base-patch32",
        manifest_path=str(manifest_path),
        strict_manifest=True,
    )

    assert loaded is not None
    assert loaded.shape == sample_embeddings.shape


def test_strict_manifest_rejects_unverified_cache_without_model(temp_embeddings):
    loaded = load_or_generate_embeddings(
        dataset_size=50,
        embeddings_path=temp_embeddings,
        texts=["song"] * 50,
        model=None,
        processor=None,
        device=None,
        strict_manifest=True,
    )

    assert loaded is None
