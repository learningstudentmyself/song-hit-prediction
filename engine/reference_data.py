"""
reference_data.py
------------------
Loads data/reference_profiles.json — the heuristic per-market feature ranges
the scoring engine compares an uploaded song against.
"""

from __future__ import annotations

import json
import os

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "reference_profiles.json")


def load_reference_profiles(path: str = _DATA_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_markets(profiles: dict) -> list[tuple[str, str]]:
    """Returns [(market_key, label), ...] for populating a UI dropdown."""
    return [(key, val.get("label", key)) for key, val in profiles["markets"].items()]


def get_market_profile(profiles: dict, market_key: str) -> dict:
    if market_key not in profiles["markets"]:
        raise KeyError(
            f"Unknown market '{market_key}'. Available: {list(profiles['markets'].keys())}"
        )
    return profiles["markets"][market_key]
