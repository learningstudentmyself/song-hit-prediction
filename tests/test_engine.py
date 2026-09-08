"""
Basic sanity test: runs the full pipeline against the synthetic test WAV
(tests/sample_test_audio.wav — generate it first with make_test_audio.py)
and checks nothing crashes and the output shape is sane, IN ALL THREE
SUPPORTED LANGUAGES. This is NOT a correctness test of the musical
judgments (we don't have licensed real songs to test against) — it's a
smoke test that the DSP + scoring + i18n code runs end-to-end without
errors.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.pipeline import analyze_song  # noqa: E402
from engine.i18n import SUPPORTED_LANGUAGES  # noqa: E402

TEST_AUDIO = os.path.join(os.path.dirname(__file__), "sample_test_audio.wav")


def run():
    assert os.path.exists(TEST_AUDIO), "Run make_test_audio.py first."

    lyrics_sample = (
        "timro maya छ mero man ma, I miss you every dashain, "
        "sapana dekhchu farkane ghar"
    )

    last_result = None
    for lang in SUPPORTED_LANGUAGES:
        result = analyze_song(
            TEST_AUDIO,
            market_key="nepali_pop",
            lyrics_text=lyrics_sample,
            lang=lang,
        )

        assert 0 <= result["overall_score_100"] <= 100
        assert len(result["breakdown"]) > 0
        assert result["lyrics"]["available"] is True
        assert isinstance(result["suggestions"], list)
        assert isinstance(result["caveats"], list) and len(result["caveats"]) >= 3
        assert result["lang"] == lang
        print(f"OK ({lang}): score={result['overall_score_100']}, "
              f"{len(result['suggestions'])} suggestion(s), "
              f"market_label='{result['market_label']}'")
        last_result = result

    print("\nFull result for the last language tested:")
    print(json.dumps(last_result, indent=2, ensure_ascii=False))
    print("\nOK: pipeline ran end-to-end without errors in all supported languages.")


if __name__ == "__main__":
    run()
