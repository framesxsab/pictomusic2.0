"""Offline reward and contextual-bandit evaluation for PictoMusic.

This module is intentionally not imported by the Streamlit app. It supports
safe evaluation of logged feedback and candidate ranking policies before any
learned policy is allowed to affect live recommendations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional

import numpy as np
import pandas as pd

from ranking import has_http, minmax_score, parse_release_year


DEFAULT_ACTION_REWARDS: dict[str, float] = {
    "shown": 0.0,
    "impression": 0.0,
    "skip": -0.10,
    "dismiss": -0.20,
    "preview_played": 0.35,
    "open": 0.55,
    "opened": 0.55,
    "selected": 1.00,
    "save": 1.20,
    "saved": 1.20,
    "share": 1.20,
    "shared": 1.20,
}

DEFAULT_LINEAR_POLICY_WEIGHTS: dict[str, float] = {
    "visual_score": 1.00,
    "india_affinity": 0.20,
    "language_match": 0.20,
    "region_match": 0.14,
    "has_preview": 0.08,
    "has_artwork": 0.02,
    "recent_release": 0.08,
    "catalog_refresh": 0.04,
    "popularity": 0.06,
}


@dataclass(frozen=True)
class OfflinePolicyValue:
    """Summary for logged-policy and optional counterfactual policy value."""

    impressions: int
    average_reward: float
    positive_action_rate: float
    ips_value: Optional[float]
    snips_value: Optional[float]
    effective_sample_size: Optional[float]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _norm(value: object) -> str:
    return str(value or "").strip().lower()


def _numeric_feature(candidates: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in candidates.columns:
        return pd.Series(default, index=candidates.index, dtype="float32")
    return pd.to_numeric(candidates[column], errors="coerce").fillna(default)


def reward_for_action(
    action: object,
    explicit_reward: object = None,
    action_rewards: Mapping[str, float] | None = None,
) -> float:
    """Return the numeric reward for an interaction row."""
    if explicit_reward is not None and str(explicit_reward).strip() != "":
        value = pd.to_numeric(pd.Series([explicit_reward]), errors="coerce").iloc[0]
        if not pd.isna(value):
            return float(value)

    rewards = action_rewards or DEFAULT_ACTION_REWARDS
    return float(rewards.get(_norm(action), 0.0))


def add_reward_column(
    interactions: pd.DataFrame,
    action_col: str = "action",
    reward_col: str = "reward",
    output_col: str = "computed_reward",
    action_rewards: Mapping[str, float] | None = None,
) -> pd.DataFrame:
    """Attach a reward column while preserving the original log data."""
    if action_col not in interactions.columns:
        raise ValueError(f"interaction log must include {action_col!r}")

    work = interactions.copy()
    explicit = work[reward_col] if reward_col in work.columns else pd.Series([None] * len(work))
    work[output_col] = [
        reward_for_action(action, reward, action_rewards)
        for action, reward in zip(work[action_col], explicit)
    ]
    return work


def estimate_policy_value(
    interactions: pd.DataFrame,
    action_col: str = "action",
    reward_col: str = "reward",
    logged_propensity_col: str = "propensity",
    target_propensity_col: str = "target_propensity",
) -> dict[str, Any]:
    """Estimate logged and target policy value from bandit feedback.

    If both propensity columns are present, IPS and self-normalized IPS are
    reported. If they are absent, the function still returns the logged average
    reward, which is useful for monitoring but not a counterfactual proof.
    """
    work = add_reward_column(
        interactions,
        action_col=action_col,
        reward_col=reward_col,
    )
    rewards = pd.to_numeric(work["computed_reward"], errors="coerce").fillna(0.0)
    warnings: list[str] = []

    ips_value: Optional[float] = None
    snips_value: Optional[float] = None
    effective_sample_size: Optional[float] = None

    if logged_propensity_col in work.columns and target_propensity_col in work.columns:
        logged = pd.to_numeric(work[logged_propensity_col], errors="coerce")
        target = pd.to_numeric(work[target_propensity_col], errors="coerce")
        valid = logged.gt(0.0) & logged.le(1.0) & target.ge(0.0) & target.le(1.0)
        invalid_count = int((~valid).sum())
        if invalid_count:
            warnings.append(f"dropped {invalid_count} rows with invalid propensities")

        if bool(valid.any()):
            importance_weights = (target[valid] / logged[valid]).astype(float)
            weighted_rewards = importance_weights * rewards[valid]
            ips_value = float(weighted_rewards.mean())
            weight_sum = float(importance_weights.sum())
            if weight_sum > 0:
                snips_value = float(weighted_rewards.sum() / weight_sum)
                denom = float((importance_weights**2).sum())
                if denom > 0:
                    effective_sample_size = float((weight_sum**2) / denom)
        else:
            warnings.append("no valid rows available for IPS evaluation")
    else:
        warnings.append("propensity columns missing; counterfactual IPS was not computed")

    result = OfflinePolicyValue(
        impressions=int(len(work)),
        average_reward=float(rewards.mean()) if len(rewards) else 0.0,
        positive_action_rate=float((rewards > 0).mean()) if len(rewards) else 0.0,
        ips_value=ips_value,
        snips_value=snips_value,
        effective_sample_size=effective_sample_size,
        warnings=warnings,
    )
    return result.to_dict()


def build_policy_features(
    candidates: pd.DataFrame,
    preferred_language: str = "any",
    preferred_region: str = "any",
) -> pd.DataFrame:
    """Build stable numeric features for offline policy scoring."""
    features = pd.DataFrame(index=candidates.index)

    score_source = "visual_score"
    if score_source not in candidates.columns:
        score_source = "similarity_score" if "similarity_score" in candidates.columns else ""
    if not score_source and "hybrid_score" in candidates.columns:
        score_source = "hybrid_score"
    features["visual_score"] = _numeric_feature(candidates, score_source) if score_source else 0.0

    features["india_affinity"] = _numeric_feature(candidates, "india_affinity")

    preferred_language = _norm(preferred_language)
    if preferred_language and preferred_language != "any" and "language" in candidates.columns:
        features["language_match"] = candidates["language"].map(_norm).eq(preferred_language).astype(float)
    else:
        features["language_match"] = 0.0

    preferred_region = _norm(preferred_region)
    if preferred_region and preferred_region != "any" and "region" in candidates.columns:
        features["region_match"] = candidates["region"].map(_norm).eq(preferred_region).astype(float)
    else:
        features["region_match"] = 0.0

    features["has_preview"] = (
        candidates["preview"].map(has_http).astype(float) if "preview" in candidates.columns else 0.0
    )
    features["has_artwork"] = (
        candidates["img"].map(has_http).astype(float) if "img" in candidates.columns else 0.0
    )

    year_col = next(
        (column for column in ("release_year", "year", "release_date", "date") if column in candidates.columns),
        "",
    )
    if year_col:
        years = candidates[year_col].map(parse_release_year).fillna(0)
        features["recent_release"] = years.ge(2025).astype(float)
    else:
        features["recent_release"] = 0.0

    if "catalog_year" in candidates.columns:
        features["catalog_refresh"] = (
            pd.to_numeric(candidates["catalog_year"], errors="coerce").fillna(0).ge(2026).astype(float)
        )
    else:
        features["catalog_refresh"] = 0.0

    if "popularity" in candidates.columns:
        features["popularity"] = minmax_score(candidates["popularity"])
    else:
        features["popularity"] = 0.0

    return features.astype("float32")


def score_linear_policy(
    candidates: pd.DataFrame,
    weights: Mapping[str, float] | None = None,
    preferred_language: str = "any",
    preferred_region: str = "any",
    output_col: str = "policy_score",
) -> pd.DataFrame:
    """Score and sort candidates with an offline linear policy."""
    policy_weights = dict(DEFAULT_LINEAR_POLICY_WEIGHTS)
    if weights:
        policy_weights.update({str(key): float(value) for key, value in weights.items()})

    features = build_policy_features(
        candidates,
        preferred_language=preferred_language,
        preferred_region=preferred_region,
    )
    scores = pd.Series(0.0, index=features.index)
    for column, weight in policy_weights.items():
        if column in features.columns:
            scores += features[column].astype(float) * float(weight)

    ranked = candidates.copy()
    ranked[output_col] = scores
    ranked.sort_values(output_col, ascending=False, inplace=True)
    return ranked.reset_index(drop=True)


def evaluate_ranked_policy(
    ranked: pd.DataFrame,
    reward_by_id: Mapping[str, float],
    item_id_col: str = "id",
    top_k: int = 10,
) -> dict[str, Any]:
    """Evaluate a ranked list against explicit item rewards."""
    if ranked.empty or top_k <= 0:
        return {
            "top_k": int(top_k),
            "mean_reward_at_k": 0.0,
            "precision_at_k": 0.0,
            "ndcg_at_k": 0.0,
            "reciprocal_rank": 0.0,
            "preview_share_at_k": 0.0,
        }

    visible = ranked.head(top_k)
    if item_id_col not in visible.columns:
        raise ValueError(f"ranked results must include {item_id_col!r}")

    rewards = [
        float(reward_by_id.get(str(item_id), 0.0))
        for item_id in visible[item_id_col].astype(str)
    ]
    discounts = np.log2(np.arange(2, len(rewards) + 2))
    dcg = float(np.sum(np.array(rewards, dtype=float) / discounts))
    ideal_rewards = sorted((float(value) for value in reward_by_id.values()), reverse=True)[: len(rewards)]
    idcg = float(np.sum(np.array(ideal_rewards, dtype=float) / discounts[: len(ideal_rewards)]))

    first_positive = next((idx for idx, reward in enumerate(rewards) if reward > 0), None)
    preview_share = (
        float(visible["preview"].map(has_http).mean()) if "preview" in visible.columns else 0.0
    )

    return {
        "top_k": int(top_k),
        "mean_reward_at_k": float(np.mean(rewards)) if rewards else 0.0,
        "precision_at_k": float(np.mean([reward > 0 for reward in rewards])) if rewards else 0.0,
        "ndcg_at_k": float(dcg / idcg) if idcg > 0 else 0.0,
        "reciprocal_rank": float(1.0 / (first_positive + 1)) if first_positive is not None else 0.0,
        "preview_share_at_k": preview_share,
    }
