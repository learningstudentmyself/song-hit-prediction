"""
lyrics_features.py
-------------------
Lyrics acquisition + analysis for Nepali / Hindi / English (and mixed) lyrics.

Design goal: work with ZERO paid APIs and ZERO required large downloads.
Everything in this file works using only the standard library + the core
requirements.txt. Two optional upgrades are supported if the user installs
requirements-optional.txt (openai-whisper, transformers, torch):

  1. Transcription: if no lyrics text is supplied but Whisper is installed,
     we transcribe the vocals from the audio file.
  2. Sentiment: if `transformers` is installed and a multilingual sentiment
     model can be downloaded, we use it. Otherwise we fall back to a small
     hand-built keyword lexicon (documented below) — cruder, but honest,
     free, offline, and instant.

IMPORTANT HONESTY NOTE (carried over from the Phase 1 report):
Free NLP tooling for Hindi is reasonably mature; free NLP tooling for Nepali
is thin. The keyword lexicons below are deliberately small starter lists,
not a substitute for a properly trained model — treat their output as a
rough signal, and expand the lexicons in data/ as you gather more lyrics.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class LyricsFeatures:
    source: str                      # "user-provided", "transcribed", or "unavailable"
    text_preview: str                # first ~200 chars, for sanity-checking in the UI
    script_mix: dict                 # {"devanagari": pct, "latin": pct, "other": pct}
    code_switch_score: float         # 0-1, how much the lyrics mix Devanagari + Latin script
    dominant_theme: Optional[str]
    theme_scores: dict                # theme -> 0-1 relative strength
    sentiment_label: Optional[str]    # "positive" / "negative" / "mixed" / "neutral"
    sentiment_score: float            # -1..1
    sentiment_method: str             # "transformer-model" or "keyword-lexicon" or "n/a"
    word_count: int

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Step 1: get lyrics text
# ---------------------------------------------------------------------------

def get_lyrics_text(lyrics_text: Optional[str] = None, audio_path: Optional[str] = None,
                     whisper_language: Optional[str] = None) -> tuple[str, str]:
    """Returns (text, source). source is 'user-provided', 'transcribed', or 'unavailable'."""
    if lyrics_text and lyrics_text.strip():
        return lyrics_text.strip(), "user-provided"

    if audio_path:
        transcribed = _try_whisper_transcribe(audio_path, whisper_language)
        if transcribed:
            return transcribed, "transcribed"

    return "", "unavailable"


def _try_whisper_transcribe(audio_path: str, language: Optional[str]) -> Optional[str]:
    try:
        import whisper  # optional dependency — see requirements-optional.txt
    except ImportError:
        return None
    try:
        # "small" is a reasonable free/local trade-off of speed vs. accuracy;
        # swap to "medium" or "large" in requirements-optional setups with a GPU.
        model = whisper.load_model("small")
        kwargs = {"language": language} if language else {}
        result = model.transcribe(audio_path, **kwargs)
        return (result.get("text") or "").strip() or None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Step 2: script mix / code-switching
# ---------------------------------------------------------------------------

_DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")
_LATIN_RE = re.compile(r"[A-Za-z]")


def analyze_script_mix(text: str) -> tuple[dict, float]:
    if not text:
        return {"devanagari": 0.0, "latin": 0.0, "other": 0.0}, 0.0

    devanagari_chars = len(_DEVANAGARI_RE.findall(text))
    latin_chars = len(_LATIN_RE.findall(text))
    total = devanagari_chars + latin_chars
    if total == 0:
        return {"devanagari": 0.0, "latin": 0.0, "other": 1.0}, 0.0

    dev_pct = devanagari_chars / total
    lat_pct = latin_chars / total
    script_mix = {
        "devanagari": round(dev_pct, 3),
        "latin": round(lat_pct, 3),
        "other": 0.0,
    }
    # Code-switch score peaks when the mix is close to 50/50, i.e. genuinely
    # bilingual lyrics — not just "mostly one language with a stray word".
    code_switch_score = round(1.0 - abs(dev_pct - lat_pct), 3)
    if total < 20:  # too little text to say anything meaningful
        code_switch_score = 0.0
    return script_mix, code_switch_score


# ---------------------------------------------------------------------------
# Step 3: theme detection (keyword lexicon, Nepali + Hindi + English)
# ---------------------------------------------------------------------------
# Deliberately small, hand-picked starter lexicons. Nepali and Hindi share the
# Devanagari script and a lot of vocabulary (Nepali draws heavily on Sanskrit/
# Hindi), so many entries are shared; a handful of distinctive function words
# are used only to *guess* which of the two a Devanagari text leans toward
# (see guess_devanagari_language below) — themes/sentiment are scored across
# both languages together since the vocabulary overlaps so heavily anyway.

THEMES = {
    "romance": [
        "love", "heart", "baby", "kiss", "forever", "beautiful", "darling",
        "माया", "मायाँ", "प्रेम", "प्यार", "इश्क़", "मोहब्बत", "दिल", "साथी", "जान",
    ],
    "heartbreak_separation": [
        "miss you", "alone", "cry", "gone", "goodbye", "tears", "broken",
        "बिदा", "बिछोड", "जुदाई", "तनहाई", "दुख", "पीर", "आँसू", "दर्द", "रुनु",
    ],
    "migration_diaspora": [
        "abroad", "foreign", "hometown", "return", "far away",
        "परदेश", "विदेश", "प्रवास", "घर फर्कन", "पर्देशी", "मुलुक",
    ],
    "ambition_struggle": [
        "dream", "fight", "rise", "struggle", "hustle", "success",
        "सपना", "लक्ष्य", "संघर्ष", "मेहनत", "हिम्मत", "मंज़िल",
    ],
    "celebration_party": [
        "party", "dance", "tonight", "celebrate", "shine", "vibe",
        "नाच", "रमाइलो", "खुशी", "जश्न", "उत्सव",
    ],
    "social_commentary": [
        "system", "government", "society", "truth", "justice", "change",
        "समाज", "सरकार", "व्यवस्था", "सत्य", "न्याय", "बदलाव",
    ],
}

_POSITIVE_WORDS = set(
    "love happy joy beautiful shine smile dream celebrate rise forever "
    "माया खुशी रमाइलो सपना जश्न न्याय हिम्मत".split()
)
_NEGATIVE_WORDS = set(
    "alone cry gone broken tears sad pain struggle goodbye lost "
    "दुख पीर आँसू बिदा जुदाई तनहाई दर्द".split()
)

# Distinctive high-frequency function words used only to guess Nepali vs.
# Hindi when the script is Devanagari (both languages share the script).
_NEPALI_MARKERS = {"छ", "छन्", "हुन्छ", "गर्छ", "थियो", "पर्छ"}
_HINDI_MARKERS = {"है", "था", "हूँ", "थे", "करता", "रहा"}


def guess_devanagari_language(text: str) -> str:
    """Best-effort guess between 'nepali' and 'hindi' for Devanagari text.
    Both languages are closely related and share the script, so this is a
    coarse heuristic based on a handful of distinctive function words, not a
    real language-ID model. Returns 'uncertain' if there isn't enough signal."""
    tokens = set(text.split())
    nepali_hits = len(tokens & _NEPALI_MARKERS)
    hindi_hits = len(tokens & _HINDI_MARKERS)
    if nepali_hits == 0 and hindi_hits == 0:
        return "uncertain"
    return "nepali" if nepali_hits >= hindi_hits else "hindi"


def analyze_themes_and_sentiment(text: str) -> tuple[Optional[str], dict, Optional[str], float, str]:
    """Returns (dominant_theme, theme_scores, sentiment_label, sentiment_score, method)."""
    if not text or len(text.strip()) < 5:
        return None, {}, None, 0.0, "n/a"

    lowered = text.lower()

    theme_scores = {}
    for theme, keywords in THEMES.items():
        hits = sum(lowered.count(kw.lower()) for kw in keywords)
        theme_scores[theme] = hits
    total_hits = sum(theme_scores.values())
    if total_hits > 0:
        theme_scores = {k: round(v / total_hits, 3) for k, v in theme_scores.items()}
        dominant_theme = max(theme_scores, key=theme_scores.get)
    else:
        dominant_theme = None

    sentiment_label, sentiment_score, method = _try_transformer_sentiment(text)
    if sentiment_label is None:
        sentiment_label, sentiment_score = _keyword_sentiment(lowered)
        method = "keyword-lexicon"

    return dominant_theme, theme_scores, sentiment_label, sentiment_score, method


def _keyword_sentiment(lowered_text: str) -> tuple[str, float]:
    pos = sum(lowered_text.count(w) for w in _POSITIVE_WORDS)
    neg = sum(lowered_text.count(w) for w in _NEGATIVE_WORDS)
    total = pos + neg
    if total == 0:
        return "neutral", 0.0
    score = (pos - neg) / total
    if score > 0.2:
        label = "positive"
    elif score < -0.2:
        label = "negative"
    else:
        label = "mixed"
    return label, round(score, 3)


def _try_transformer_sentiment(text: str) -> tuple[Optional[str], float, str]:
    try:
        from transformers import pipeline  # optional dependency
    except ImportError:
        return None, 0.0, "n/a"
    try:
        clf = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
        )
        result = clf(text[:512])[0]
        label = result["label"].lower()
        score = float(result["score"])
        signed = score if "pos" in label else (-score if "neg" in label else 0.0)
        return label, round(signed, 3), "transformer-model"
    except Exception:
        return None, 0.0, "n/a"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def extract_lyrics_features(lyrics_text: Optional[str] = None, audio_path: Optional[str] = None,
                             whisper_language: Optional[str] = None) -> LyricsFeatures:
    text, source = get_lyrics_text(lyrics_text, audio_path, whisper_language)

    if source == "unavailable":
        return LyricsFeatures(
            source="unavailable",
            text_preview="",
            script_mix={"devanagari": 0.0, "latin": 0.0, "other": 0.0},
            code_switch_score=0.0,
            dominant_theme=None,
            theme_scores={},
            sentiment_label=None,
            sentiment_score=0.0,
            sentiment_method="n/a",
            word_count=0,
        )

    script_mix, code_switch_score = analyze_script_mix(text)
    dominant_theme, theme_scores, sentiment_label, sentiment_score, method = \
        analyze_themes_and_sentiment(text)

    return LyricsFeatures(
        source=source,
        text_preview=text[:200],
        script_mix=script_mix,
        code_switch_score=code_switch_score,
        dominant_theme=dominant_theme,
        theme_scores=theme_scores,
        sentiment_label=sentiment_label,
        sentiment_score=sentiment_score,
        sentiment_method=method,
        word_count=len(text.split()),
    )
