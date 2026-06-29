"""Lightweight image context cues for recommendation query building."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class ImageContext:
    labels: List[str]
    music_cues: List[str]
    metrics: Dict[str, float]


def _append_unique(values: List[str], *items: str) -> None:
    seen = set(values)
    for item in items:
        if item and item not in seen:
            values.append(item)
            seen.add(item)


def analyze_image_context(image: Image.Image) -> ImageContext:
    """Extract cheap visual tone cues without adding another ML model.

    These cues are intentionally broad. They enrich the CLIP text bridge for
    mood retrieval while keeping deployment cost unchanged.
    """
    sample = image.convert("RGB").resize((96, 96), Image.Resampling.BILINEAR)
    arr = np.asarray(sample, dtype=np.float32) / 255.0

    red = arr[:, :, 0]
    green = arr[:, :, 1]
    blue = arr[:, :, 2]
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    max_rgb = arr.max(axis=2)
    min_rgb = arr.min(axis=2)
    saturation = np.where(max_rgb > 0, (max_rgb - min_rgb) / np.maximum(max_rgb, 1e-6), 0.0)

    brightness = float(luminance.mean())
    contrast = float(luminance.std())
    colorfulness = float(saturation.mean())
    warmth = float(red.mean() - blue.mean())

    grad_y, grad_x = np.gradient(luminance)
    edge_strength = np.sqrt(grad_x * grad_x + grad_y * grad_y)
    detail = float((edge_strength > 0.08).mean())

    labels: List[str] = []
    cues: List[str] = []

    if brightness < 0.28:
        _append_unique(labels, "dark lighting")
        _append_unique(cues, "moody", "nocturnal", "intense")
    elif brightness > 0.68:
        _append_unique(labels, "bright lighting")
        _append_unique(cues, "upbeat", "open", "happy")

    if warmth > 0.08:
        _append_unique(labels, "warm color temperature")
        _append_unique(cues, "warm", "romantic", "acoustic")
    elif warmth < -0.08:
        _append_unique(labels, "cool color temperature")
        _append_unique(cues, "calm", "modern", "soothing")

    if colorfulness < 0.18:
        _append_unique(labels, "muted color")
        _append_unique(cues, "minimal", "soft", "acoustic")
    elif colorfulness > 0.48:
        _append_unique(labels, "vivid color")
        _append_unique(cues, "energetic", "festive", "danceable")

    if contrast < 0.16:
        _append_unique(labels, "soft contrast")
        _append_unique(cues, "soothing", "gentle", "calm")
    elif contrast > 0.28:
        _append_unique(labels, "high contrast")
        _append_unique(cues, "dramatic", "confident", "intense")

    if detail < 0.08:
        _append_unique(labels, "simple composition")
        _append_unique(cues, "minimal", "focus", "calm")
    elif detail > 0.22:
        _append_unique(labels, "busy composition")
        _append_unique(cues, "energetic", "urban", "party")

    return ImageContext(
        labels=labels,
        music_cues=cues,
        metrics={
            "brightness": round(brightness, 4),
            "contrast": round(contrast, 4),
            "colorfulness": round(colorfulness, 4),
            "warmth": round(warmth, 4),
            "detail": round(detail, 4),
        },
    )
