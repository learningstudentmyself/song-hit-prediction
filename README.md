# Hit Song Predictor

Upload a song, get a **fit score** against recent Nepali / Indian market patterns, a
feature-by-feature breakdown, and concrete suggestions — built entirely on free,
open-source tools (see `requirements.txt` / `requirements-optional.txt`).

This is Phase 2 of the HitSongPrediction project. Phase 1 was a research report on
what actually correlates with hit songs (see `docs/phase1-analysis-report.md` if you
copied it in, or your Claude project). Everything in this engine's scoring logic
traces back to that report — the reference ranges, the feature weights, and the
suggestion text all cite specific findings from it.

## Quick start

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Web UI
streamlit run app.py

# or, command line
python cli.py --list-markets
python cli.py --audio yoursong.mp3 --market nepali_pop --lyrics lyrics.txt
```

No API keys, no accounts, no paid services. First run of the Streamlit app opens a
browser tab automatically.

### Optional upgrades (still free, but bigger downloads)

```bash
pip install -r requirements-optional.txt
```

This adds:
- **Whisper** — auto-transcribe lyrics straight from the audio (Nepali + Hindi supported)
- **transformers + torch** — swaps the built-in keyword-based sentiment analysis for a
  real multilingual transformer model

The app works fine without these — it just falls back to text you paste/upload and a
simpler keyword-based lyrics analysis.

## Language

The UI and CLI can show every label, feature comment, suggestion, and caveat in
**English, Nepali, or Hindi** — pick it from the "Language" dropdown at the top of
the Streamlit app, or pass `--lang ne` / `--lang hi` to `cli.py` (default `en`).

The scoring logic itself (`engine/scoring.py`) is completely language-agnostic — it
only outputs structured keys (which feature, which status, which theme). All actual
English/Nepali/Hindi text lives in one place, `engine/i18n.py`, and is applied as the
very last step (`i18n.render_result()`, called from `engine/pipeline.py`). That means:

- Adding a new language means editing `engine/i18n.py` only — no scoring logic changes.
- The Nepali and Hindi strings are a solid best-effort translation, written directly
  (not machine-translated at request time), but **have not been reviewed by a native
  speaker for tone/naturalness** — the same "heuristic, worth polishing" spirit as the
  rest of this project. Search `engine/i18n.py` for `"ne":` / `"hi":` to find and edit
  any string.

## What the score actually means (read this)

**It is a "fit score," not a "hit probability."** It tells you how closely your
song's *measurable* audio and lyrics features match what recent songs in your chosen
market tend to look like. It is explicitly NOT trying to claim it knows whether your
song will be a hit — the Phase 1 research was clear that things like artist fame,
marketing budget, a viral dance/choreography moment, and release timing are often
just as or more decisive than the song itself, and none of that is visible in an
audio file. Every result includes a caveats section restating this.

## How it works (end to end)

```
Upload/record song (+ optional lyrics)
        │
        ▼
Audio Analyzer (engine/audio_features.py, librosa)
  tempo, energy, loudness, key/mode, intro length,
  hook repetition, brightness, acousticness, ...
        │
Lyrics Analyzer (engine/lyrics_features.py)
  theme detection, sentiment, language-mix / code-switching
  (transcribes from audio via Whisper if no lyrics given & installed)
        │
        ▼
Reference Library (data/reference_profiles.json)
  heuristic "typical recent hit" ranges per market
  (Nepali Pop, Bollywood/Hindi, Punjabi Crossover, Generic)
        │
        ▼
Scoring Engine (engine/scoring.py)
  compares your song's features to the market's ranges,
  produces a 0-100 fit score + per-feature breakdown
        │
        ▼
Suggestions + caveats, shown in the Streamlit UI or CLI
```

## Project structure

```
hit-song-predictor/
├── app.py                        # Streamlit UI — the main way to use this
├── cli.py                        # command-line alternative
├── engine/
│   ├── audio_features.py         # librosa-based DSP feature extraction
│   ├── lyrics_features.py        # transcription + theme/sentiment/language-mix
│   ├── reference_data.py         # loads data/reference_profiles.json
│   ├── scoring.py                # comparison + scoring — LANGUAGE-AGNOSTIC (keys/codes only)
│   ├── i18n.py                   # all English/Nepali/Hindi text lives here
│   └── pipeline.py               # ties the above together (analyze_song(..., lang=...))
├── data/
│   └── reference_profiles.json   # per-market target ranges (see caveat below)
├── tests/
│   ├── make_test_audio.py        # generates a synthetic (non-copyrighted) test WAV
│   └── test_engine.py            # smoke test — runs the full pipeline end to end
├── requirements.txt              # core deps (audio analysis + UI)
└── requirements-optional.txt     # Whisper / transformers upgrades
```

Run the smoke test any time to confirm your install works, without needing a real
song file:

```bash
python tests/make_test_audio.py
python tests/test_engine.py
```

## The features it extracts (and how honest each one is)

All of these are DSP-computed **proxies**, not Spotify's proprietary algorithms —
Spotify's own "audio features" API was restricted for new developer apps in
November 2024, so there's no free official ground truth to copy anyway. See the
docstring at the top of `engine/audio_features.py` for the full detail per feature.
Roughly, in order of how much to trust them:

- **Solid, standard DSP** (trust these): tempo, duration, loudness (via `pyloudnorm`,
  real integrated LUFS), spectral brightness, key/mode estimate.
- **Reasonable proxies** (directionally useful): danceability, energy, acousticness,
  speechiness, hook-repetition score.
- **Rougher heuristics** (treat as a rough signal only): intro length (approximates
  "when the track gets going" via an energy threshold — it can't tell the difference
  between an instrumental build and an actual vocal entrance without a vocal
  separation model), section count.

## Improving the reference library (the honest next step)

`data/reference_profiles.json` currently holds **heuristic starting ranges** written
from the qualitative findings in the Phase 1 report — not fitted from a real,
labeled dataset of measured audio features. That's because building that dataset
requires running `engine.audio_features.extract_audio_features()` over a real,
licensed collection of recent hit and non-hit songs for each market, which needs
audio access this project doesn't ship with (for copyright reasons — no song audio
is bundled here).

To upgrade it: gather audio for, say, 50-100 recent songs per market you care about
(a mix of hits and non-hits, per the "compare bottom-quartile vs top-quartile views"
approach discussed in the project), run them all through `extract_audio_features()`,
and replace the `ideal_low`/`ideal_high`/`soft_min`/`soft_max` numbers in the JSON
with the actual 25th/75th and 5th/95th percentiles you measure. The scoring engine
doesn't need any code changes for this — it just reads whatever is in the JSON file.

## Extending the lyrics analysis

`engine/lyrics_features.py` has a deliberately small, hand-built keyword lexicon for
Nepali/Hindi/English theme and sentiment detection — free, instant, no downloads,
but crude. It's designed to be replaced or augmented, not treated as final:

- Add more words to the `THEMES`, `_POSITIVE_WORDS`, `_NEGATIVE_WORDS` dictionaries
  as you see real lyrics come through.
- Install `requirements-optional.txt` to get a real multilingual transformer model
  for sentiment instead (`_try_transformer_sentiment` already wires this in — it's
  used automatically if `transformers` is installed).
- The Nepali-vs-Hindi language guess (`guess_devanagari_language`) is a coarse
  function-word heuristic — both languages share the Devanagari script and a lot of
  vocabulary, so treat its output as a hint, not ground truth.

## What this does NOT do (by design)

- It does not access Spotify, YouTube, or any streaming service — you provide the
  audio file directly.
- It does not use any paid API — everything runs locally once dependencies are
  installed.
- It does not, and cannot, measure marketing, artist fame, or virality potential.
  These were flagged repeatedly in the Phase 1 research as major hit-making factors
  that simply aren't present in an audio file — the UI says this explicitly in every
  result rather than pretending otherwise.
