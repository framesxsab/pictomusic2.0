"""Validate Hugging Face Docker Space deployment readiness."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DOCKERFILE = ROOT / "Dockerfile"
REQUIREMENTS = ROOT / "requirements.txt"
ATTRIBUTES = ROOT / ".gitattributes"
DOCKERIGNORE = ROOT / ".dockerignore"
DATASET = ROOT / "Music.csv"
EMBEDDINGS = ROOT / "song_embeddings_fp16.npy"
MANIFEST = ROOT / "song_embeddings_fp16.npy.manifest.json"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_space_metadata(readme: str) -> dict[str, str]:
    lines = readme.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    metadata: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata


def file_starts_with_lfs_pointer(path: Path) -> bool:
    with path.open("rb") as handle:
        prefix = handle.read(128)
    return prefix.startswith(b"version https://git-lfs.github.com/spec/v1")


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def warn(condition: bool, message: str, warnings: list[str]) -> None:
    if not condition:
        warnings.append(message)


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []

    for path in [README, DOCKERFILE, REQUIREMENTS, ATTRIBUTES, DOCKERIGNORE, DATASET, EMBEDDINGS, MANIFEST]:
        require(path.exists(), f"missing required file: {path.relative_to(ROOT)}", failures)

    if failures:
        print_report(failures, warnings)
        return 1

    readme = read_text(README)
    metadata = parse_space_metadata(readme)
    require(metadata.get("sdk") == "docker", "README metadata must set sdk: docker", failures)
    require(metadata.get("app_port") == "7860", "README metadata must set app_port: 7860", failures)

    dockerfile = read_text(DOCKERFILE)
    require("useradd -m -u 1000 user" in dockerfile, "Dockerfile must create Hugging Face UID 1000 user", failures)
    require("COPY --chown=user:user" in dockerfile, "Dockerfile COPY steps must use --chown=user:user", failures)
    require(re.search(r"\bEXPOSE\s+7860\b", dockerfile) is not None, "Dockerfile must expose port 7860", failures)
    require("--server.port=7860" in dockerfile, "Dockerfile CMD must run Streamlit on port 7860", failures)
    require("--server.address=0.0.0.0" in dockerfile, "Dockerfile CMD must bind to 0.0.0.0", failures)

    requirements = read_text(REQUIREMENTS)
    for dependency in ["streamlit", "torch", "transformers", "faiss-cpu", "Pillow", "requests"]:
        require(re.search(rf"(^|\n){re.escape(dependency)}([<>=~!]|$)", requirements) is not None,
                f"requirements.txt missing runtime dependency: {dependency}", failures)

    dockerignore = read_text(DOCKERIGNORE)
    for pattern in [".git/", ".venv/", "tests/", "datasets/", "output/", ".cursor/", ".claude/"]:
        warn(pattern in dockerignore, f".dockerignore should exclude {pattern}", warnings)

    attributes = read_text(ATTRIBUTES)
    require("*.npy filter=lfs" in attributes, ".gitattributes must LFS-track .npy files", failures)
    require("*.csv filter=lfs" in attributes, ".gitattributes must LFS-track .csv files", failures)
    require(not file_starts_with_lfs_pointer(DATASET), "Music.csv is only a Git LFS pointer locally", failures)
    require(not file_starts_with_lfs_pointer(EMBEDDINGS), "song_embeddings_fp16.npy is only a Git LFS pointer locally", failures)

    manifest = json.loads(read_text(MANIFEST))
    embeddings = np.load(EMBEDDINGS, mmap_mode="r", allow_pickle=False)
    csv_rows = count_csv_rows(DATASET)

    require(manifest.get("dataset_size") == csv_rows,
            f"manifest dataset_size {manifest.get('dataset_size')} != Music.csv rows {csv_rows}", failures)
    require(tuple(manifest.get("embedding_shape", [])) == tuple(embeddings.shape),
            f"manifest embedding_shape {manifest.get('embedding_shape')} != embeddings shape {embeddings.shape}", failures)
    require(manifest.get("embedding_dtype") == str(embeddings.dtype),
            f"manifest embedding_dtype {manifest.get('embedding_dtype')} != embeddings dtype {embeddings.dtype}", failures)
    require(embeddings.shape[0] == csv_rows,
            f"embedding rows {embeddings.shape[0]} != Music.csv rows {csv_rows}", failures)
    require(embeddings.ndim == 2 and embeddings.shape[1] == 512,
            f"expected CLIP embedding shape (*, 512), got {embeddings.shape}", failures)

    print_report(failures, warnings, csv_rows=csv_rows, embedding_shape=tuple(embeddings.shape))
    return 1 if failures else 0


def print_report(
    failures: list[str],
    warnings: list[str],
    *,
    csv_rows: int | None = None,
    embedding_shape: tuple[int, ...] | None = None,
) -> None:
    if failures:
        print("HF deployment readiness: FAIL")
    else:
        print("HF deployment readiness: PASS")

    if csv_rows is not None:
        print(f"catalog_rows={csv_rows}")
    if embedding_shape is not None:
        print(f"embedding_shape={embedding_shape}")

    for failure in failures:
        print(f"FAIL: {failure}")
    for warning in warnings:
        print(f"WARN: {warning}")


if __name__ == "__main__":
    raise SystemExit(main())
