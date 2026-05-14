"""
PictoMusic Embeddings Module
Handles text embedding generation, caching, and FAISS index construction.
Run standalone: python -m src.embeddings --dataset Music.csv --output embeddings.npy
"""

import argparse
import logging
import os
from pathlib import Path
from typing import Callable, List, Optional

import faiss
import numpy as np
import torch
from transformers import CLIPModel, CLIPProcessor

from config import (
    CLIP_MODEL_NAME,
    DATASET_PATH,
    EMBEDDING_BATCH_SIZE,
    EMBEDDINGS_PATH,
    MAX_TOKEN_LENGTH,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@torch.no_grad()
def generate_text_embeddings(
    texts: List[str],
    model: CLIPModel,
    processor: CLIPProcessor,
    device: torch.device,
    batch_size: int = EMBEDDING_BATCH_SIZE,
    max_length: int = MAX_TOKEN_LENGTH,
) -> np.ndarray:
    """Batch-encode texts into L2-normalized CLIP embeddings."""
    all_embeddings = []
    total_batches = (len(texts) + batch_size - 1) // batch_size

    logging.info("Generating text embeddings (%d texts, %d batches)...", len(texts), total_batches)
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
            logging.info("  Batch %d / %d", batch_num, total_batches)

    result = torch.cat(all_embeddings, dim=0).numpy()
    logging.info("Generated embeddings: shape %s", result.shape)
    return result


@torch.no_grad()
def generate_image_embedding(
    image,
    model: CLIPModel,
    processor: CLIPProcessor,
    device: torch.device,
) -> Optional[np.ndarray]:
    """Encode a single PIL Image into an L2-normalized CLIP embedding."""
    try:
        inputs = processor(images=image, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        features = model.get_image_features(**inputs)
        features = features / features.norm(p=2, dim=-1, keepdim=True)
        return features.cpu().numpy()
    except Exception as e:
        logging.error("Error generating image embedding: %s", e)
        return None


def load_or_generate_embeddings(
    dataset_size: int,
    embeddings_path: str,
    texts: Optional[List[str]],
    model: Optional[CLIPModel],
    processor: Optional[CLIPProcessor],
    device: Optional[torch.device],
) -> Optional[np.ndarray]:
    """Load cached embeddings or regenerate if shape doesn't match."""
    if os.path.exists(embeddings_path):
        try:
            embeddings = np.load(embeddings_path)
            if len(embeddings) == dataset_size:
                logging.info("Loaded cached embeddings from %s (%d vectors)", embeddings_path, len(embeddings))
                return embeddings
            else:
                logging.warning(
                    "Embeddings size mismatch (cached: %d, dataset: %d) — regenerating.",
                    len(embeddings), dataset_size
                )
        except Exception as e:
            logging.error("Error loading embeddings from %s: %s — regenerating.", embeddings_path, e)

    if texts is None or model is None or processor is None or device is None:
        logging.error("Cannot generate embeddings — missing model/texts.")
        return None

    embeddings = generate_text_embeddings(texts, model, processor, device)
    if embeddings is not None:
        try:
            np.save(embeddings_path, embeddings.astype(np.float16))
            logging.info("Saved embeddings to %s", embeddings_path)
        except Exception as e:
            logging.error("Error saving embeddings: %s", e)

    return embeddings


def build_faiss_index(embeddings: np.ndarray) -> Optional[faiss.IndexFlatIP]:
    """Create and populate a FAISS inner-product index."""
    try:
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings.astype("float32"))
        logging.info("FAISS index built: %d vectors, %d dimensions", index.ntotal, dimension)
        return index
    except Exception as e:
        logging.error("Error building FAISS index: %s", e)
        return None


if __name__ == "__main__":
    import pandas as pd
    from preprocess import build_enhanced_description, run_preprocessing

    parser = argparse.ArgumentParser(description="PictoMusic Embedding Generator")
    parser.add_argument("--dataset", default=DATASET_PATH, help="Path to dataset CSV")
    parser.add_argument("--output", default=EMBEDDINGS_PATH, help="Output .npy path")
    parser.add_argument("--model", default=CLIP_MODEL_NAME, help="CLIP model name")
    args = parser.parse_args()

    logging.info("Loading CLIP model: %s", args.model)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    clip_model = CLIPModel.from_pretrained(args.model).to(device)
    clip_processor = CLIPProcessor.from_pretrained(args.model)
    clip_model.eval()

    logging.info("Loading and preprocessing dataset: %s", args.dataset)
    df = run_preprocessing(existing_csv=args.dataset)
    if df.empty:
        logging.error("Preprocessing returned empty dataset — aborting.")
        raise SystemExit(1)
    texts = df.apply(build_enhanced_description, axis=1).tolist()
    logging.info("Sample descriptions:\n  %s", "\n  ".join(texts[:5]))

    embeddings = generate_text_embeddings(texts, clip_model, clip_processor, device)
    np.save(args.output, embeddings.astype(np.float16))
    logging.info("Done. Saved %d embeddings to %s", len(embeddings), args.output)
