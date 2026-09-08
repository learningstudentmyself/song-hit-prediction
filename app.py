"""
Hit Song Predictor — Streamlit UI

Run with:
    streamlit run app.py

Upload a song (mp3/wav/m4a/flac), optionally paste or upload lyrics, pick a
target market and a display language (English / Nepali / Hindi), and get a
fit score + feature breakdown + suggestions — all shown in the language you
picked.

See README.md for setup, what the score does/doesn't mean, and how to
extend this (real reference dataset, transformer-based sentiment, Whisper
transcription, more languages in engine/i18n.py).
"""

import os
import tempfile

import streamlit as st

from engine.pipeline import analyze_song
from engine.reference_data import load_reference_profiles, list_markets
from engine.i18n import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, ui, market_label

st.set_page_config(page_title="Hit Song Predictor", page_icon="🎵", layout="wide")

# --- Language picker lives at the very top since it drives every other label ---
lang = st.selectbox(
    ui("language", DEFAULT_LANGUAGE),
    options=list(SUPPORTED_LANGUAGES.keys()),
    format_func=lambda k: SUPPORTED_LANGUAGES[k],
    index=0,
    key="lang_picker",
)

st.title(f"🎵 {ui('app_title', lang)}")
st.caption(ui("app_caption", lang))

profiles = load_reference_profiles()
markets = list_markets(profiles)

with st.sidebar:
    st.header(ui("settings", lang))
    market_key = st.selectbox(
        ui("target_market", lang),
        options=[m[0] for m in markets],
        format_func=lambda k: market_label(k, lang, fallback=dict(markets)[k]),
        index=0,
    )
    st.markdown("---")
    st.subheader(ui("lyrics_optional", lang))
    lyrics_mode_options = [
        ui("lyrics_mode_paste", lang),
        ui("lyrics_mode_upload", lang),
        ui("lyrics_mode_transcribe", lang),
        ui("lyrics_mode_skip", lang),
    ]
    lyrics_mode = st.radio(ui("lyrics_mode_question", lang), options=lyrics_mode_options, index=0)

    pasted_lyrics = ""
    lyrics_file = None
    whisper_language = None
    if lyrics_mode == ui("lyrics_mode_paste", lang):
        pasted_lyrics = st.text_area(ui("paste_lyrics_label", lang), height=180)
    elif lyrics_mode == ui("lyrics_mode_upload", lang):
        lyrics_file = st.file_uploader(ui("lyrics_file_label", lang), type=["txt"])
    elif lyrics_mode == ui("lyrics_mode_transcribe", lang):
        whisper_language = st.selectbox(
            ui("whisper_lang_label", lang),
            options=[None, "ne", "hi", "en"],
            format_func=lambda x: {"ne": "Nepali", "hi": "Hindi", "en": "English", None: "Auto-detect"}[x],
        )
        st.caption(ui("whisper_caption", lang))
    st.markdown("---")
    st.caption(ui("reference_caption", lang))

uploaded_audio = st.file_uploader(ui("upload_label", lang), type=["mp3", "wav", "m4a", "flac", "ogg"])

analyze_clicked = st.button(ui("analyze_button", lang), type="primary", disabled=uploaded_audio is None)


def _score_color(score: float) -> str:
    if score >= 75:
        return "🟢"
    if score >= 55:
        return "🟡"
    return "🔴"


if analyze_clicked and uploaded_audio is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_audio.name)[1]) as tmp:
        tmp.write(uploaded_audio.read())
        tmp_path = tmp.name

    lyrics_text = None
    use_lyrics = True
    if lyrics_mode == ui("lyrics_mode_paste", lang) and pasted_lyrics.strip():
        lyrics_text = pasted_lyrics
    elif lyrics_mode == ui("lyrics_mode_upload", lang) and lyrics_file is not None:
        lyrics_text = lyrics_file.read().decode("utf-8", errors="ignore")
    elif lyrics_mode == ui("lyrics_mode_skip", lang):
        use_lyrics = False
    # "Try auto-transcribe" leaves lyrics_text=None and use_lyrics=True,
    # which triggers the Whisper attempt inside the pipeline.

    try:
        with st.spinner(ui("analyzing", lang)):
            result = analyze_song(
                tmp_path,
                market_key=market_key,
                lyrics_text=lyrics_text,
                use_lyrics=use_lyrics,
                whisper_language=whisper_language,
                lang=lang,
            )
    except Exception as e:
        st.error(ui("analysis_failed", lang, error=e))
        st.stop()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        score = result["overall_score_100"]
        st.metric(
            f"{_score_color(score)} {ui('fit_score_prefix', lang)} — {result['market_label']}",
            f"{score:.1f} / 100",
        )
        st.progress(min(100, max(0, int(score))) / 100)
        st.caption(ui("audio_only_subscore", lang, score=result["audio_score_100"]))
        if result["lyrics"]["available"]:
            st.caption(ui("lyrics_subscore", lang, score=result["lyrics"]["lyrics_score_100"]))

    with col2:
        st.subheader(ui("suggestions_header", lang))
        if result["suggestions"]:
            for s in result["suggestions"]:
                st.markdown(f"- {s}")
        else:
            st.markdown(ui("no_suggestions", lang))
        if result.get("mode_note"):
            st.caption(result["mode_note"])

    st.markdown(f"### {ui('feature_breakdown_header', lang)}")
    rows = result["breakdown"]
    st.dataframe(
        [
            {
                ui("col_feature", lang): r["label"],
                ui("col_value", lang): r["value"],
                ui("col_range", lang): f"{r['ideal_low']}–{r['ideal_high']}",
                ui("col_score", lang): f"{r['score']:.2f}",
                ui("col_status", lang): r["status_label"],
            }
            for r in rows
        ],
        use_container_width=True,
        hide_index=True,
    )

    if result["lyrics"]["available"]:
        st.markdown(f"### {ui('lyrics_analysis_header', lang)}")
        lyr = result["lyrics"]
        lcol1, lcol2 = st.columns(2)
        with lcol1:
            st.write(f"**{ui('lyrics_source', lang)}:** {lyr['source']}")
            st.write(f"**{ui('lyrics_dominant_theme', lang)}:** {lyr['dominant_theme_label']}")
            st.write(f"**{ui('lyrics_theme_match', lang)}:** {lyr['theme_match_with_market']:.2f}")
            st.write(f"**{ui('lyrics_code_switch', lang)}:** {lyr['code_switch_score']:.2f}")
        with lcol2:
            st.write(f"**{ui('lyrics_sentiment', lang)}:** {lyr['sentiment_label_localized']} ({lyr['sentiment_score']:.2f})")
            st.write(f"**{ui('lyrics_sentiment_method', lang)}:** {lyr['sentiment_method']}")
            st.write(f"**{ui('lyrics_word_count', lang)}:** {lyr.get('word_count')}")
        with st.expander(ui("theme_scores_expander", lang)):
            st.json(lyr["theme_scores_labeled"])
    else:
        st.info(ui("no_lyrics_analyzed", lang))

    with st.expander(ui("raw_features_expander", lang)):
        st.json(result["audio_features"])

    st.markdown(f"### {ui('caveats_header', lang)}")
    for c in result["caveats"]:
        st.markdown(f"- {c}")

elif uploaded_audio is None:
    st.info(ui("upload_prompt", lang))
