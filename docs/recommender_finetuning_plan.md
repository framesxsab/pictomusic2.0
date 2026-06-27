# PictoMusic Recommender Fine-Tuning Plan

## Current State

PictoMusic already uses a production-style staged recommender:

1. CLIP image encoding for the uploaded image.
2. CLIP text embeddings for every song description.
3. FAISS candidate retrieval over the precomputed song embeddings.
4. Zero-shot scene and mood classification.
5. Hybrid reranking for Indian language, region, mood, freshness, popularity, preview availability, and duplicate suppression.

This is close to the public pattern Meta describes for Instagram recommendations: retrieval, first-stage ranking, later ranking stages, and final reranking. Meta also describes using caching, precomputation, and two-tower neural networks for scalable retrieval. The public Meta material is about Instagram Explore, not a full implementation disclosure for Instagram Stories music recommendations, so PictoMusic should borrow the architecture pattern rather than assume exact private details.

Primary references:

- Meta Engineering, "Scaling the Instagram Explore recommendations system": https://engineering.fb.com/2023/08/09/ml-applications/scaling-instagram-explore-recommendations-system/
- Meta AI, "The AI behind unconnected content recommendations on Facebook and Instagram": https://ai.meta.com/blog/ai-unconnected-content-recommendations-facebook-instagram/
- Hugging Face Transformers CLIP docs: https://huggingface.co/docs/transformers/en/model_doc/clip
- OpenAI CLIP paper: https://arxiv.org/abs/2103.00020
- FAISS documentation: https://faiss.ai/index.html
- Google ML recommendation overview and reranking docs: https://developers.google.com/machine-learning/recommendation/overview/candidate-generation and https://developers.google.com/machine-learning/recommendation/dnn/re-ranking

## What Should Not Be Fine-Tuned Yet

Do not fine-tune the base CLIP model in the current repo state. The dataset has song metadata, audio features, region/language tags, and previews, but it does not contain the supervised examples needed for a reliable image-to-song model update:

- uploaded image or story context,
- songs shown,
- song selected,
- preview played,
- save/share/add-to-story action,
- skip/dismiss action,
- timestamp, language, and region context.

Without those labels, fine-tuning CLIP can easily overfit metadata text and make the current Indian retrieval quality worse. The safer path is to improve cache safety, offline evaluation, and reranking first.

## Safe Enhancement Implemented Now

The embedding cache now has a manifest file tied to:

- dataset size,
- embedding shape and dtype,
- CLIP model name,
- SHA-256 fingerprint of the exact song-description corpus used to generate the embeddings.

This protects future model or embedding experiments. If a fine-tuned CLIP model, changed song-description schema, or changed dataset is used with `PICTOMUSIC_STRICT_EMBEDDING_MANIFEST=1`, the app will reject stale cached embeddings and regenerate instead of silently serving mismatched vectors.

Expected manifest path:

```bash
song_embeddings_fp16.npy.manifest.json
```

Regenerate embeddings safely:

```bash
python -m src.embeddings --dataset Music.csv --output song_embeddings_fp16.npy --model openai/clip-vit-base-patch32
```

Enable strict validation in deployment after the manifest is present:

```bash
PICTOMUSIC_STRICT_EMBEDDING_MANIFEST=1
```

The offline evaluation path also supports RL-style policy evaluation without
changing production ranking. `src/offline_rl.py` provides:

- reward mapping for actions such as preview plays, selections, saves, shares, skips, and dismissals,
- logged-policy reward summaries,
- inverse propensity scoring and self-normalized IPS when logs contain `propensity` and `target_propensity`,
- offline linear policy scoring for candidate reranking experiments.

Run it through the existing evaluator:

```bash
python -m src.evaluation --interaction-log path\to\interactions.csv
```

This is a safety layer, not a live learner. It should only graduate into the
app after real feedback logs prove that a target policy beats the current
hybrid ranking on offline value, golden checks, and manual image smoke tests.

## Recommended Fine-Tuning Roadmap

### Phase 1: Offline Weight Calibration

Goal: improve ranking without changing CLIP.

Steps:

1. Expand `evaluation/golden_recommendations.json` with 30 to 50 image-intent scenarios:
   - Bollywood romance,
   - Tamil/Telugu festival,
   - Punjabi party,
   - Bengali monsoon,
   - devotional temple,
   - Bhojpuri wedding,
   - Gujarati garba,
   - Marathi folk.
2. Add more synthetic ranking fixtures with hard negatives:
   - high visual score but wrong language,
   - correct language but no preview,
   - duplicate variants,
   - stale global hit versus fresh Indian track.
3. Grid search current weights from `src/config.py` against golden checks:
   - language,
   - region,
   - India affinity,
   - preview,
   - freshness,
   - popularity,
   - scene genre boost.
4. Promote new weights only when all current golden checks remain green and new cases improve.

This is the lowest-risk improvement and mirrors production reranking practice.

### Phase 2: Metadata-Enriched Embedding Regeneration

Goal: improve candidate retrieval while keeping the same CLIP model.

Steps:

1. Improve `build_enhanced_description()` with stronger Indian context phrases, for example:
   - "Bollywood romantic Hindi song for rainy evening",
   - "Tamil festival dance track",
   - "Punjabi night drive party song".
2. Regenerate `song_embeddings_fp16.npy`.
3. Let the manifest validate that the new embedding file matches the new text corpus.
4. Compare golden checks and manual smoke tests before deployment.

This changes retrieval behavior, so do it only after Phase 1 baselines are expanded.

### Phase 3: Lightweight Learned Reranker

Goal: approximate the ranking layer used by larger recommendation systems without replacing CLIP.

Required data:

- golden labels or user feedback labels,
- candidate features from current retrieval,
- positive and negative examples.

Candidate features:

- CLIP similarity,
- image mood confidence,
- language match,
- region match,
- India affinity,
- preview availability,
- popularity,
- freshness,
- duplicate group size,
- scene-to-genre match.

Model options:

- logistic regression,
- gradient boosted trees,
- small multilayer perceptron.

Deployment rule:

- keep it behind an environment flag until it beats current ranking in offline checks and manual image smoke tests.

### Phase 4: CLIP or Two-Tower Fine-Tuning

Goal: learn a PictoMusic-specific embedding space.

Only start this after collecting real image/story-song interaction data. Use contrastive learning with positive image-song pairs and hard negatives. A two-tower approach is the right direction for scale: one tower encodes user/image/story context, the other encodes song candidates. This follows the same broad retrieval idea Meta describes publicly, while staying feasible for PictoMusic.

Training data shape:

```text
image_id, image_features_or_path, song_id, action, language, region, timestamp
```

Positive actions:

- selected song,
- preview played,
- opened Spotify or YouTube,
- saved/shared.

Negative actions:

- shown but skipped,
- dismissed,
- low dwell time.

Do not ship a fine-tuned model unless it improves:

- precision at 5,
- preview-visible share,
- language/region match rate,
- duplicate rate,
- manual quality for Indian scenarios.
