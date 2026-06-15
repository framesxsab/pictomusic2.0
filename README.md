---
title: Pictomusic
emoji: "\U0001F3B5"
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
---

# PictoMusic 3.0 - AI Music Discovery

## Quality Gates

Run the standard tests:

```bash
python -m pytest -q
```

Run the India-first golden recommendation checks:

```bash
python -m src.evaluation
```

The golden checks validate:

- Real catalog coverage for Bollywood, Tamil, Punjabi, Marathi, Gujarati, Bengali, devotional, and Bhojpuri scenarios.
- Preview availability where the source catalog exposes previews.
- Track-link availability where preview audio is not available.
- Preview-first result balancing, while preserving very strong non-preview matches.
- Duplicate-song suppression so the visible recommendation tab does not repeat the same song.
- Deterministic hybrid-ranking fixtures that protect India, language, region, preview, and uniqueness behavior from regression.
