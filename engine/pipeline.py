"""
pipeline.py
-----------
Single entry point that ties together audio_features + lyrics_features +
reference_data + scoring. Both the Streamlit UI (app.py) and the CLI
(cli.py) call analyze_song() so the logic only lives in one place.
"""

from __future__ import annotations

from typing import Optional

from .audio_features import extract_audio_features
from .lyrics_features import extract_lyrics_features
from .reference_data import load_reference_profiles, get_market_profile
from .scoring import compute_score
from .i18n import render_result, DEFAULT_LANGUAGE


def analyze_song(audio_path: str, market_key: str = "generic_south_asian_pop",
                  lyrics_text: Optional[str] = None,
                  use_lyrics: bool = True,
                  whisper_language: Optional[str] = None,
                  lang: str = DEFAULT_LANGUAGE) -> dict:
    """Runs the full pipeline on one audio file and returns a FULLY LOCALIZED
    result dict (labels, comments, suggestions, caveats all in `lang` —
    one of "en", "ne", "hi"). The underlying scoring logic itself
    (engine/scoring.py) is language-agnostic; engine/i18n.render_result()
    does the localization as the last step here."""

    audio_features = extract_audio_features(audio_path)

    lyrics_features = None
    if use_lyrics:
        lyrics_features = extract_lyrics_features(
            lyrics_text=lyrics_text,
            audio_path=audio_path,
            whisper_language=whisper_language,
        )

    profiles = load_reference_profiles()
    market_profile = get_market_profile(profiles, market_key)

    result = compute_score(audio_features, lyrics_features, market_profile)
    result["audio_features"] = audio_features.to_dict()
    result["lyrics_features"] = lyrics_features.to_dict() if lyrics_features else None
    result["market_key"] = market_key
    result["market_label"] = market_profile.get("label", market_key)

    return render_result(result, lang)
