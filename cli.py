"""
Command-line alternative to the Streamlit UI — useful for batch-checking
several files, or if you just don't want to run a web server.

Usage:
    python cli.py --audio mysong.mp3 --market nepali_pop --lyrics lyrics.txt
    python cli.py --audio mysong.mp3 --market bollywood_hindi --no-lyrics --lang hi
    python cli.py --list-markets
    python cli.py --list-languages
"""

import argparse
import json
import sys

from engine.pipeline import analyze_song
from engine.reference_data import load_reference_profiles, list_markets
from engine.i18n import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, ui


def main():
    parser = argparse.ArgumentParser(description="Analyze a song's fit against a market's recent hit patterns.")
    parser.add_argument("--audio", help="Path to the audio file (mp3/wav/m4a/flac).")
    parser.add_argument("--market", default="generic_south_asian_pop", help="Market key (see --list-markets).")
    parser.add_argument("--lyrics", help="Path to a .txt file with lyrics.")
    parser.add_argument("--no-lyrics", action="store_true", help="Skip lyrics analysis entirely.")
    parser.add_argument("--whisper-lang", default=None, help="Language hint for Whisper transcription (e.g. 'ne', 'hi').")
    parser.add_argument("--lang", default=DEFAULT_LANGUAGE, choices=list(SUPPORTED_LANGUAGES.keys()),
                         help="Display language for suggestions/output: en, ne, or hi.")
    parser.add_argument("--list-markets", action="store_true", help="List available market keys and exit.")
    parser.add_argument("--list-languages", action="store_true", help="List available display languages and exit.")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of a formatted summary.")
    args = parser.parse_args()

    if args.list_markets:
        profiles = load_reference_profiles()
        for key, label in list_markets(profiles):
            print(f"{key:30s} {label}")
        return

    if args.list_languages:
        for key, label in SUPPORTED_LANGUAGES.items():
            print(f"{key:5s} {label}")
        return

    if not args.audio:
        parser.error("--audio is required (or use --list-markets / --list-languages)")

    lyrics_text = None
    if args.lyrics:
        with open(args.lyrics, "r", encoding="utf-8") as f:
            lyrics_text = f.read()

    result = analyze_song(
        args.audio,
        market_key=args.market,
        lyrics_text=lyrics_text,
        use_lyrics=not args.no_lyrics,
        whisper_language=args.whisper_lang,
        lang=args.lang,
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    lang = args.lang
    print(f"\n=== {result['market_label']} ===")
    print(f"{ui('fit_score_prefix', lang)}: {result['overall_score_100']:.1f} / 100  "
          f"({ui('audio_only_subscore', lang, score=result['audio_score_100'])})")
    if result["lyrics"]["available"]:
        print(f"{ui('lyrics_subscore', lang, score=result['lyrics']['lyrics_score_100'])}  "
              f"({ui('lyrics_dominant_theme', lang)}: {result['lyrics']['dominant_theme_label']})")

    print(f"\n--- {ui('feature_breakdown_header', lang)} ---")
    for r in result["breakdown"]:
        print(f"  {r['label']:25s} {ui('col_value', lang)}={r['value']!s:<10} "
              f"{ui('col_range', lang)}={r['ideal_low']}-{r['ideal_high']:<8} "
              f"{ui('col_score', lang)}={r['score']:.2f}  ({r['status_label']})")
    if result.get("mode_note"):
        print(f"\n{result['mode_note']}")

    print(f"\n--- {ui('suggestions_header', lang)} ---")
    if result["suggestions"]:
        for s in result["suggestions"]:
            print(f"  - {s}")
    else:
        print(f"  ({ui('no_suggestions', lang)})")

    print(f"\n--- {ui('caveats_header', lang)} ---")
    for c in result["caveats"]:
        print(f"  - {c}")
    print()


if __name__ == "__main__":
    sys.exit(main())
