"""
scoring.py
----------
Compares a song's extracted audio + lyrics features against a market's
reference profile (data/reference_profiles.json) and produces:
  - an overall 0-100 "fit score" (NOT a "hit probability" — see README on why)
  - a feature-by-feature breakdown (structured: feature key, value, ideal
    range, per-feature score, status code)
  - suggestion TRIGGERS (structured: which feature/status, or which lyrics
    condition, fired) rather than English sentences
  - caveat KEYS rather than English sentences

IMPORTANT: this module is deliberately LANGUAGE-AGNOSTIC. It never contains
a user-facing English sentence — everything here is a key/code that
engine/i18n.py turns into English, Nepali, or Hindi text at render time.
See engine/i18n.render_result() for that step.
"""

from __future__ import annotations

from typing import Optional

from .audio_features import AudioFeatures
from .lyrics_features import LyricsFeatures

# ---------------------------------------------------------------------------
# Generic feature scorer
# ---------------------------------------------------------------------------

def score_feature(value: float, cfg: dict) -> tuple[float, str]:
    """Piecewise-linear score: 1.0 inside [ideal_low, ideal_high], ramping
    down to 0.0 at soft_min / soft_max, 0.0 beyond those. Returns (score, status)."""
    ideal_low, ideal_high = cfg["ideal_low"], cfg["ideal_high"]
    soft_min, soft_max = cfg["soft_min"], cfg["soft_max"]

    if value is None:
        return 0.5, "unknown"  # neutral score when a feature couldn't be measured

    if ideal_low <= value <= ideal_high:
        return 1.0, "ideal"

    if value < ideal_low:
        if value <= soft_min:
            return 0.0, "below_range"
        span = ideal_low - soft_min
        score = (value - soft_min) / span if span > 0 else 1.0
        return max(0.0, min(1.0, score)), "below_ideal"

    # value > ideal_high
    if value >= soft_max:
        return 0.0, "above_range"
    span = soft_max - ideal_high
    score = (soft_max - value) / span if span > 0 else 1.0
    return max(0.0, min(1.0, score)), "above_ideal"


# ---------------------------------------------------------------------------
# Main scoring entry point — returns structured, language-agnostic data
# ---------------------------------------------------------------------------

def compute_score(audio: AudioFeatures, lyrics: Optional[LyricsFeatures],
                   market_profile: dict) -> dict:
    audio_dict = audio.to_dict()
    breakdown = []
    weighted_sum = 0.0
    weight_total = 0.0
    suggestion_triggers = []  # list of dicts: {"type": ..., ...params}

    for feature, cfg in market_profile["features"].items():
        value = audio_dict.get(feature)
        score, status = score_feature(value, cfg)
        weight = cfg["weight"]
        weighted_sum += score * weight
        weight_total += weight

        breakdown.append({
            "feature": feature,
            "value": value,
            "ideal_low": cfg["ideal_low"],
            "ideal_high": cfg["ideal_high"],
            "score": round(score, 3),
            "status": status,
            "weight": weight,
        })

        if score < 0.6 and status not in ("ideal", "unknown"):
            suggestion_triggers.append({"type": "feature", "feature": feature, "status": status})

    # Mode (major/minor) — weak, documented signal; small additive nudge, not
    # a fully weighted feature.
    mode_bonus_weight = market_profile.get("mode_preference", {}).get("minor_bonus", 0.0)
    mode_info = None
    if mode_bonus_weight > 0 and audio.mode in ("major", "minor"):
        mode_score = 1.0 if audio.mode == "minor" else 0.5
        w = mode_bonus_weight * 4  # keep its influence small relative to core features
        weighted_sum += mode_score * w
        weight_total += w
        mode_info = {"key": audio.key, "mode": audio.mode, "confidence": audio.key_confidence}

    audio_score_100 = (weighted_sum / weight_total * 100) if weight_total > 0 else 50.0

    # --- Lyrics contribution (only if lyrics are available) -----------------
    lyrics_section = {"available": False}
    final_score_100 = audio_score_100

    if lyrics is not None and lyrics.source != "unavailable" and lyrics.dominant_theme:
        lyrics_cfg = market_profile.get("lyrics", {})
        resonant = set(market_profile.get("resonant_themes", []))
        theme_match = sum(
            v for k, v in lyrics.theme_scores.items() if k in resonant
        )
        theme_score_100 = min(1.0, theme_match) * 100

        code_switch_bonus_weight = lyrics_cfg.get("code_switch_bonus_weight", 0.0)
        code_switch_100 = lyrics.code_switch_score * 100

        theme_w = lyrics_cfg.get("theme_weight", 0.5)
        switch_w = code_switch_bonus_weight
        total_lyrics_w = theme_w + switch_w
        if total_lyrics_w > 0:
            lyrics_score_100 = (theme_score_100 * theme_w + code_switch_100 * switch_w) / total_lyrics_w
        else:
            lyrics_score_100 = theme_score_100

        # Blend: audio carries most of the weight (per report Section 5 — audio
        # alone is already the ceiling of what's measurable; lyrics refine it).
        AUDIO_BLEND_WEIGHT = 0.75
        LYRICS_BLEND_WEIGHT = 0.25
        final_score_100 = (
            audio_score_100 * AUDIO_BLEND_WEIGHT + lyrics_score_100 * LYRICS_BLEND_WEIGHT
        )

        if theme_match < 0.15:
            suggestion_triggers.append({
                "type": "lyrics_theme_mismatch",
                "theme": lyrics.dominant_theme,
                "resonant_themes": sorted(resonant),
            })
        if code_switch_bonus_weight > 0.2 and lyrics.code_switch_score < 0.15:
            suggestion_triggers.append({"type": "lyrics_code_switch"})

        lyrics_section = {
            "available": True,
            "source": lyrics.source,
            "dominant_theme": lyrics.dominant_theme,
            "theme_scores": lyrics.theme_scores,
            "resonant_themes": sorted(resonant),
            "theme_match_with_market": round(theme_match, 3),
            "code_switch_score": lyrics.code_switch_score,
            "sentiment_label": lyrics.sentiment_label,
            "sentiment_score": lyrics.sentiment_score,
            "sentiment_method": lyrics.sentiment_method,
            "lyrics_score_100": round(lyrics_score_100, 1),
            "word_count": lyrics.word_count if hasattr(lyrics, "word_count") else None,
        }

    caveat_keys = ["fit_not_probability", "non_audio_factors", "heuristic_reference"]
    if lyrics is None or lyrics.source == "unavailable":
        caveat_keys.append("no_lyrics")

    return {
        "overall_score_100": round(final_score_100, 1),
        "audio_score_100": round(audio_score_100, 1),
        "audio_breakdown": breakdown,
        "mode_info": mode_info,
        "lyrics": lyrics_section,
        "suggestion_triggers": suggestion_triggers,
        "caveat_keys": caveat_keys,
    }
