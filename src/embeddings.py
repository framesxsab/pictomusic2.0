"""
PictoMusic Embeddings Module
Handles text embedding generation, caching, and FAISS index construction.
Run standalone: python -m src.embeddings --dataset Music.csv --output embeddings.npy
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, List, Optional

import numpy as np

try:
    import torch
except ImportError:
    torch = None

try:
    from transformers import CLIPModel, CLIPProcessor
except ImportError:
    CLIPModel = None
    CLIPProcessor = None

from config import (
    CLIP_MODEL_NAME,
    DATASET_PATH,
    EMBEDDING_BATCH_SIZE,
    EMBEDDINGS_MANIFEST_PATH,
    EMBEDDINGS_PATH,
    MAX_TOKEN_LENGTH,
    STRICT_EMBEDDING_MANIFEST,
)

logger = logging.getLogger(__name__)
MANIFEST_VERSION = 1


def _no_grad():
    if torch is not None:
        return torch.no_grad()

    def decorator(func):
        return func

    return decorator


def fingerprint_texts(texts: List[str]) -> str:
    """Return a stable fingerprint for the exact text corpus used for embeddings."""
    digest = hashlib.sha256()
    for text in texts:
        digest.update(str(text).encode("utf-8", errors="replace"))
        digest.update(b"\0")
    return digest.hexdigest()


def build_embeddings_manifest(
    *,
    dataset_size: int,
    embedding_shape: tuple[int, ...],
    embedding_dtype: str,
    model_name: str,
    text_fingerprint: str,
) -> dict:
    """Build metadata that ties an embedding file to its model and text corpus."""
    return {
        "version": MANIFEST_VERSION,
        "dataset_size": int(dataset_size),
        "embedding_shape": [int(value) for value in embedding_shape],
        "embedding_dtype": str(embedding_dtype),
        "model_name": str(model_name),
        "text_fingerprint": str(text_fingerprint),
    }


def read_embeddings_manifest(path: str) -> Optional[dict]:
    """Read an embedding manifest if it exists and is valid JSON."""
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else None
    except Exception as e:
        logger.warning("Could not read embeddings manifest %s: %s", path, e)
        return None


def write_embeddings_manifest(path: str, manifest: dict) -> None:
    """Persist an embedding manifest next to the generated cache."""
    try:
        manifest_path = Path(path)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
            f.write("\n")
        logger.info("Saved embeddings manifest to %s", path)
    except Exception as e:
        logger.warning("Could not save embeddings manifest %s: %s", path, e)


def embedding_manifest_matches(
    manifest: dict,
    *,
    dataset_size: int,
    embedding_shape: tuple[int, ...],
    model_name: str,
    text_fingerprint: str,
    embedding_dtype: Optional[str] = None,
) -> tuple[bool, str]:
    """Validate that cached embeddings match the current corpus and model."""
    expected_shape = [int(value) for value in embedding_shape]
    checks = {
        "version": MANIFEST_VERSION,
        "dataset_size": int(dataset_size),
        "embedding_shape": expected_shape,
        "model_name": str(model_name),
        "text_fingerprint": str(text_fingerprint),
    }
    if embedding_dtype is not None:
        checks["embedding_dtype"] = str(embedding_dtype)
    for key, expected in checks.items():
        actual = manifest.get(key)
        if actual != expected:
            return False, f"{key} mismatch: manifest={actual!r}, current={expected!r}"
    return True, "manifest matches"


def normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
    """Return float32 L2-normalized embeddings for cosine/IP retrieval."""
    values = np.asarray(embeddings, dtype=np.float32)
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    norms = np.where(norms > 0.0, norms, 1.0)
    return values / norms


@_no_grad()
def generate_text_embeddings(
    texts: List[str],
    model: CLIPModel,
    processor: CLIPProcessor,
    device: torch.device,
    batch_size: int = EMBEDDING_BATCH_SIZE,
    max_length: int = MAX_TOKEN_LENGTH,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> np.ndarray:
    """Batch-encode texts into L2-normalized CLIP embeddings."""
    if torch is None:
        raise RuntimeError("PyTorch is required to generate CLIP text embeddings.")

    all_embeddings = []
    total_batches = (len(texts) + batch_size - 1) // batch_size

    logger.info("Generating text embeddings (%d texts, %d batches)...", len(texts), total_batches)
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        inputs = processor(
            text=batch,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_length,
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        embeddings = model.get_text_features(**inputs)
        embeddings = embeddings / embeddings.norm(p=2, dim=-1, keepdim=True)
        all_embeddings.append(embeddings.cpu())

        batch_num = i // batch_size
        if batch_num % 100 == 0 and batch_num > 0:
            logger.info("  Batch %d / %d", batch_num, total_batches)

        if progress_callback:
            progress_callback(min(i + batch_size, len(texts)), len(texts))

    result = torch.cat(all_embeddings, dim=0).numpy()
    logger.info("Generated embeddings: shape %s", result.shape)
    return result


@_no_grad()
def generate_image_embedding(
    image,
    model: CLIPModel,
    processor: CLIPProcessor,
    device: torch.device,
) -> Optional[np.ndarray]:
    """Encode a single PIL Image into an L2-normalized CLIP embedding."""
    if torch is None:
        logger.error("PyTorch is required to generate CLIP image embeddings.")
        return None

    try:
        inputs = processor(images=image, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        features = model.get_image_features(**inputs)
        features = features / features.norm(p=2, dim=-1, keepdim=True)
        return features.cpu().numpy()
    except Exception as e:
        logger.error("Error generating image embedding: %s", e)
        return None


def load_or_generate_embeddings(
    dataset_size: int,
    embeddings_path: str,
    texts: Optional[List[str]],
    model: Optional[CLIPModel],
    processor: Optional[CLIPProcessor],
    device: Optional[torch.device],
    model_name: str = CLIP_MODEL_NAME,
    manifest_path: Optional[str] = None,
    strict_manifest: bool = STRICT_EMBEDDING_MANIFEST,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Optional[np.ndarray]:
    """Load cached embeddings or regenerate if shape doesn't match."""
    manifest_path = manifest_path or EMBEDDINGS_MANIFEST_PATH
    text_fingerprint = fingerprint_texts(texts) if texts is not None else None

    if os.path.exists(embeddings_path):
        try:
            embeddings = np.load(embeddings_path, allow_pickle=False)
            if len(embeddings) == dataset_size:
                manifest = read_embeddings_manifest(manifest_path)
                if manifest and text_fingerprint is not None:
                    matches, reason = embedding_manifest_matches(
                        manifest,
                        dataset_size=dataset_size,
                        embedding_shape=tuple(embeddings.shape),
                        model_name=model_name,
                        text_fingerprint=text_fingerprint,
                        embedding_dtype=str(embeddings.dtype),
                    )
                    if matches:
                        logger.info(
                            "Loaded cached embeddings from %s (%d vectors, manifest verified)",
                            embeddings_path,
                            len(embeddings),
                        )
                        return embeddings
                    logger.warning("Embeddings manifest mismatch (%s) - regenerating.", reason)
                elif strict_manifest:
                    logger.warning("Embeddings manifest missing or unverifiable - regenerating.")
                else:
                    logger.info(
                        "Loaded cached embeddings from %s (%d vectors, legacy manifest mode)",
                        embeddings_path,
                        len(embeddings),
                    )
                    return embeddings
            else:
                logger.warning(
                    "Embeddings size mismatch (cached: %d, dataset: %d) - regenerating.",
                    len(embeddings), dataset_size
                )
        except Exception as e:
            logger.error("Error loading embeddings from %s: %s - regenerating.", embeddings_path, e)

    if texts is None or model is None or processor is None or device is None:
        logger.error("Cannot generate embeddings - missing model/texts.")
        return None

    embeddings = generate_text_embeddings(
        texts, model, processor, device, progress_callback=progress_callback
    )
    if embeddings is not None:
        try:
            saved_embeddings = embeddings.astype(np.float16)
            np.save(embeddings_path, saved_embeddings)
            logger.info("Saved embeddings to %s", embeddings_path)
            if text_fingerprint is not None:
                manifest = build_embeddings_manifest(
                    dataset_size=dataset_size,
                    embedding_shape=tuple(saved_embeddings.shape),
                    embedding_dtype=str(saved_embeddings.dtype),
                    model_name=model_name,
                    text_fingerprint=text_fingerprint,
                )
                write_embeddings_manifest(manifest_path, manifest)
        except Exception as e:
            logger.error("Error saving embeddings: %s", e)

    return embeddings


def build_faiss_index(embeddings: np.ndarray) -> Optional[Any]:
    """Create and populate a FAISS inner-product index."""
    try:
        import faiss

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(normalize_embeddings(embeddings))
        logger.info("FAISS index built: %d vectors, %d dimensions", index.ntotal, dimension)
        return index
    except ImportError as e:
        logger.error(
            "FAISS is not installed for this Python interpreter. "
            "Install faiss-cpu from requirements.txt or run the repo venv.",
        )
        logger.debug("FAISS import error: %s", e)
        return None
    except Exception as e:
        logger.error("Error building FAISS index: %s", e)
        return None


if __name__ == "__main__":
    import pandas as pd
    from preprocess import build_enhanced_description, run_preprocessing

    if torch is None or CLIPModel is None or CLIPProcessor is None:
        raise SystemExit(
            "Generating embeddings requires torch and transformers. "
            "Install requirements.txt or run the repo virtual environment."
        )

    parser = argparse.ArgumentParser(description="PictoMusic Embedding Generator")
    parser.add_argument("--dataset", default=DATASET_PATH, help="Path to dataset CSV")
    parser.add_argument("--output", default=EMBEDDINGS_PATH, help="Output .npy path")
    parser.add_argument("--model", default=CLIP_MODEL_NAME, help="CLIP model name")
    args = parser.parse_args()

    logger.info("Loading CLIP model: %s", args.model)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    clip_model = CLIPModel.from_pretrained(args.model).to(device)
    clip_processor = CLIPProcessor.from_pretrained(args.model)
    clip_model.eval()

    logger.info("Loading and preprocessing dataset: %s", args.dataset)
    df = run_preprocessing(existing_csv=args.dataset)
    if df.empty:
        logger.error("Preprocessing returned empty dataset - aborting.")
        raise SystemExit(1)
    texts = df.apply(build_enhanced_description, axis=1).tolist()
    logger.info("Sample descriptions:\n  %s", "\n  ".join(texts[:5]))

    embeddings = generate_text_embeddings(texts, clip_model, clip_processor, device)
    saved_embeddings = embeddings.astype(np.float16)
    np.save(args.output, saved_embeddings)
    manifest = build_embeddings_manifest(
        dataset_size=len(texts),
        embedding_shape=tuple(saved_embeddings.shape),
        embedding_dtype=str(saved_embeddings.dtype),
        model_name=args.model,
        text_fingerprint=fingerprint_texts(texts),
    )
    write_embeddings_manifest(f"{args.output}.manifest.json", manifest)
    logger.info("Done. Saved %d embeddings to %s", len(embeddings), args.output)
