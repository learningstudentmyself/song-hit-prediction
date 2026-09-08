"""
i18n.py
-------
All display-language logic lives here, and ONLY here. engine/scoring.py stays
language-agnostic — it outputs structured data (feature keys, status codes,
theme keys, caveat keys) instead of English sentences. This module turns that
structured data into English, Nepali, or Hindi text.

HONESTY NOTE: the Nepali and Hindi strings below are a solid best-effort
translation (not machine-translated at request time — written directly), but
they have NOT been reviewed by a native speaker for tone/naturalness. Treat
them the same way the rest of this project treats its heuristic parts:
usable and directionally correct, worth polishing once a native speaker can
review the copy. Search for "ne":/"hi": below to find and edit any string.
"""

from __future__ import annotations

SUPPORTED_LANGUAGES = {
    "en": "English",
    "ne": "नेपाली (Nepali)",
    "hi": "हिंदी (Hindi)",
}

DEFAULT_LANGUAGE = "en"


def _pick(d: dict, lang: str) -> str:
    return d.get(lang, d.get(DEFAULT_LANGUAGE, ""))


# ---------------------------------------------------------------------------
# Feature labels
# ---------------------------------------------------------------------------

FEATURE_LABELS = {
    "tempo_bpm":             {"en": "Tempo", "ne": "गति (टेम्पो)", "hi": "गति (टेम्पो)"},
    "danceability_proxy":    {"en": "Danceability", "ne": "नाच्न मिल्ने गुण", "hi": "डांस-योग्यता"},
    "energy":                {"en": "Energy", "ne": "ऊर्जा", "hi": "ऊर्जा"},
    "loudness_lufs":         {"en": "Loudness", "ne": "आवाजको स्तर", "hi": "तेज़ी (लाउडनेस)"},
    "acousticness_proxy":    {"en": "Acousticness", "ne": "एकुस्टिकपन", "hi": "एकॉस्टिकनेस"},
    "speechiness_proxy":     {"en": "Speechiness", "ne": "बोली-जस्तो अंश", "hi": "स्पीच जैसा अंश"},
    "intro_length_sec":      {"en": "Intro length", "ne": "सुरुवातको लम्बाइ", "hi": "इंट्रो की लंबाई"},
    "hook_repetition_score": {"en": "Hook repetition", "ne": "हुकको पुनरावृत्ति", "hi": "हुक की पुनरावृत्ति"},
    "brightness":            {"en": "Brightness", "ne": "उज्यालोपन (ब्राइटनेस)", "hi": "चमक (ब्राइटनेस)"},
    "duration_sec":          {"en": "Song duration", "ne": "गीतको अवधि", "hi": "गाने की अवधि"},
}


def feature_label(feature: str, lang: str) -> str:
    return _pick(FEATURE_LABELS.get(feature, {"en": feature}), lang)


# ---------------------------------------------------------------------------
# Status labels + generic per-feature comment template
# ---------------------------------------------------------------------------

STATUS_LABELS = {
    "ideal":       {"en": "ideal", "ne": "आदर्श दायरामा", "hi": "आदर्श सीमा में"},
    "below_ideal": {"en": "below ideal", "ne": "आदर्शभन्दा कम", "hi": "आदर्श से कम"},
    "above_ideal": {"en": "above ideal", "ne": "आदर्शभन्दा बढी", "hi": "आदर्श से अधिक"},
    "below_range": {"en": "well below range", "ne": "दायराभन्दा धेरै कम", "hi": "सीमा से बहुत कम"},
    "above_range": {"en": "well above range", "ne": "दायराभन्दा धेरै बढी", "hi": "सीमा से बहुत अधिक"},
    "unknown":     {"en": "unknown", "ne": "अज्ञात", "hi": "अज्ञात"},
}

_COMMENT_TEMPLATE = {
    "en": "{label} ({value}) is {status} for this market ({low}–{high}).",
    "ne": "{label} ({value}) यस बजारको लागि {status} छ ({low}–{high})।",
    "hi": "{label} ({value}) इस बाज़ार के लिए {status} है ({low}–{high})।",
}

_COMMENT_TEMPLATE_IDEAL = {
    "en": "{label} ({value}) is within the range typical of recent hits in this market.",
    "ne": "{label} ({value}) यस बजारका हालैका हिट गीतहरूको सामान्य दायराभित्र छ।",
    "hi": "{label} ({value}) इस बाज़ार के हालिया हिट गानों की सामान्य सीमा के भीतर है।",
}

_COMMENT_TEMPLATE_UNKNOWN = {
    "en": "{label} could not be measured.",
    "ne": "{label} मापन गर्न सकिएन।",
    "hi": "{label} मापा नहीं जा सका।",
}


def feature_comment(feature: str, value, status: str, ideal_low, ideal_high, lang: str) -> str:
    label = feature_label(feature, lang)
    if status == "ideal":
        return _pick(_COMMENT_TEMPLATE_IDEAL, lang).format(label=label, value=value)
    if status == "unknown":
        return _pick(_COMMENT_TEMPLATE_UNKNOWN, lang).format(label=label)
    status_label = _pick(STATUS_LABELS.get(status, {}), lang)
    return _pick(_COMMENT_TEMPLATE, lang).format(
        label=label, value=value, status=status_label, low=ideal_low, high=ideal_high
    )


# ---------------------------------------------------------------------------
# Suggestions (feature-triggered)
# ---------------------------------------------------------------------------

FEATURE_SUGGESTIONS = {
    ("tempo_bpm", "below_ideal"): {
        "en": "Tempo is slower than what's currently working in this market — consider a slightly faster tempo, or make sure the slower tempo is a deliberate ballad choice rather than a default.",
        "ne": "गति यस बजारमा अहिले चलिरहेको भन्दा ढिलो छ — अलि छिटो गति सोच्नुहोस्, वा ढिलो गति जानाजानी ब्यालेडका लागि हो भन्ने पक्का गर्नुहोस्।",
        "hi": "गति इस बाज़ार में अभी चल रहे रुझान से धीमी है — थोड़ी तेज़ गति पर विचार करें, या सुनिश्चित करें कि धीमी गति जानबूझकर बैलेड के लिए चुनी गई है।",
    },
    ("tempo_bpm", "above_ideal"): {
        "en": "Tempo runs faster than the current sweet spot for this market — double check it doesn't feel rushed or lose danceability at this speed.",
        "ne": "गति यस बजारको हालैको उपयुक्त दायराभन्दा छिटो छ — यो हतारिएको जस्तो नलागोस् वा यस गतिमा नाच्न मिल्ने गुण नगुमोस् भनी जाँच्नुहोस्।",
        "hi": "गति इस बाज़ार की मौजूदा उपयुक्त सीमा से तेज़ है — जांच लें कि यह जल्दबाज़ी जैसी न लगे या इस गति पर डांस-योग्यता कम न हो।",
    },
    ("danceability_proxy", "below_ideal"): {
        "en": "Rhythmic groove/beat regularity is weaker than recent hits in this market — danceability is the single most consistent audio predictor of popularity in the research, so tightening the beat/groove is high-leverage.",
        "ne": "लयबद्ध ग्रूभ/बिटको नियमितता यस बजारका हालैका हिटहरूभन्दा कमजोर छ — अनुसन्धानअनुसार नाच्न मिल्ने गुण नै लोकप्रियताको सबैभन्दा भरपर्दो सङ्केत हो, त्यसैले बिट/ग्रूभ कस्नु प्रभावकारी हुन्छ।",
        "hi": "लयबद्ध ग्रूव/बीट की नियमितता इस बाज़ार के हालिया हिट गानों से कमज़ोर है — शोध के अनुसार डांस-योग्यता लोकप्रियता का सबसे सुसंगत संकेतक है, इसलिए बीट/ग्रूव को कसना सबसे असरदार कदम है।",
    },
    ("danceability_proxy", "above_ideal"): {
        "en": "Danceability proxy is unusually high — worth a listen to confirm it doesn't feel mechanical or lose musicality.",
        "ne": "नाच्न मिल्ने गुण असामान्य रूपमा उच्च छ — यो यान्त्रिक जस्तो नलागोस् वा संगीतात्मकता नगुमोस् भनी सुनेर पक्का गर्नुहोस्।",
        "hi": "डांस-योग्यता असामान्य रूप से अधिक है — सुनकर पुष्टि करें कि यह मशीनी न लगे या संगीतात्मकता कम न हो।",
    },
    ("energy", "below_ideal"): {
        "en": "Overall energy is lower than typical hits in this market — consider a fuller arrangement, more layered instrumentation, or a bigger dynamic lift into the chorus.",
        "ne": "समग्र ऊर्जा यस बजारका सामान्य हिटहरूभन्दा कम छ — बढी भरिएको संयोजन, थप तहगत बाजा, वा कोरसमा ठूलो उठान सोच्नुहोस्।",
        "hi": "समग्र ऊर्जा इस बाज़ार के सामान्य हिट गानों से कम है — अधिक भरा हुआ अरेंजमेंट, अधिक परतदार वाद्ययंत्र, या कोरस में बड़ा उभार जोड़ने पर विचार करें।",
    },
    ("energy", "above_ideal"): {
        "en": "Energy is very high throughout — consider adding a quieter contrast section (e.g. a stripped-back bridge) so the high-energy parts land harder by comparison.",
        "ne": "सुरुदेखि अन्त्यसम्म ऊर्जा धेरै उच्च छ — शान्त कन्ट्रास्ट खण्ड (जस्तै सरल ब्रिज) थप्नुहोस् ताकि उच्च-ऊर्जा भागहरू तुलनात्मक रूपमा बढी प्रभावकारी लागून्।",
        "hi": "शुरू से अंत तक ऊर्जा बहुत अधिक है — एक शांत कंट्रास्ट सेक्शन (जैसे हल्का ब्रिज) जोड़ने पर विचार करें ताकि उच्च-ऊर्जा हिस्से तुलना में और असरदार लगें।",
    },
    ("loudness_lufs", "below_ideal"): {
        "en": "The master is quieter than the modern streaming-competitive loudness range — consider a louder, more polished final master.",
        "ne": "मास्टर आधुनिक स्ट्रिमिङ-प्रतिस्पर्धी आवाज-स्तरभन्दा शान्त छ — बढी चर्को र पालिश गरिएको अन्तिम मास्टर सोच्नुहोस्।",
        "hi": "मास्टर आधुनिक स्ट्रीमिंग-प्रतिस्पर्धी लाउडनेस सीमा से शांत है — अधिक तेज़ और पॉलिश किया हुआ अंतिम मास्टर बनाने पर विचार करें।",
    },
    ("loudness_lufs", "above_ideal"): {
        "en": "The master is louder/more compressed than typical — check it isn't clipping or losing dynamic feel.",
        "ne": "मास्टर सामान्यभन्दा बढी चर्को/कम्प्रेस्ड छ — यो क्लिप नभएको वा डाइनामिक अनुभव नगुमेको जाँच्नुहोस्।",
        "hi": "मास्टर सामान्य से अधिक तेज़/कंप्रेस्ड है — जांच लें कि यह क्लिप न हो रहा हो या डायनामिक अहसास न खो रहा हो।",
    },
    ("acousticness_proxy", "above_range"): {
        "en": "Sounds more raw/acoustic than most current hits in this market, which tend to favor a more produced, processed sound — consider more layered/electronic production elements.",
        "ne": "यस बजारका धेरैजसो हालैका हिटहरू बढी प्रोडक्स्ड ध्वनि रुचाउँछन्, तर यो गीत तुलनात्मक रूपमा बढी कच्चा/एकुस्टिक सुनिन्छ — थप तहगत/इलेक्ट्रोनिक प्रोडक्सन तत्वहरू सोच्नुहोस्।",
        "hi": "इस बाज़ार के अधिकतर हालिया हिट गाने अधिक प्रोसेस्ड ध्वनि पसंद करते हैं, जबकि यह गाना तुलनात्मक रूप से अधिक कच्चा/एकॉस्टिक लगता है — अधिक परतदार/इलेक्ट्रॉनिक प्रोडक्शन तत्वों पर विचार करें।",
    },
    ("speechiness_proxy", "above_range"): {
        "en": "Vocal delivery reads as more talk-like/noisy than sung — heavy spoken-word sections have been linked to lower replayability; consider more melodic vocal delivery in key sections.",
        "ne": "स्वर प्रस्तुति गाइएको भन्दा बढी बोलिएको/हल्ला जस्तो लाग्छ — धेरै बोलिएको खण्डले पुनः सुन्ने दर घटाउन सक्छ; मुख्य भागहरूमा बढी सुरिलो स्वर प्रस्तुति सोच्नुहोस्।",
        "hi": "स्वर प्रस्तुति गाए जाने की बजाय बोले जाने/शोर जैसी लगती है — अधिक बोलचाल वाले हिस्से दोबारा सुने जाने की दर घटा सकते हैं; मुख्य हिस्सों में अधिक मधुर स्वर प्रस्तुति पर विचार करें।",
    },
    ("intro_length_sec", "above_ideal"): {
        "en": "Intro runs longer than the current norm — recent hits in this market open on vocals/hook within about 5 seconds. A long instrumental build risks skips on streaming and doesn't clip well for Reels/TikTok/Shorts.",
        "ne": "सुरुवात हालको सामान्य लम्बाइभन्दा लामो छ — यस बजारका हालैका हिटहरू लगभग ५ सेकेन्डभित्रै स्वर/हुकबाट सुरु हुन्छन्। लामो वाद्य-सुरुवातले स्ट्रिमिङमा स्किप हुने जोखिम बढाउँछ र रिल्स/टिकटक/शर्ट्सका लागि राम्रो क्लिप बन्दैन।",
        "hi": "इंट्रो मौजूदा मानक से लंबा है — इस बाज़ार के हालिया हिट गाने लगभग 5 सेकंड के भीतर ही स्वर/हुक से शुरू हो जाते हैं। लंबा वाद्य-प्रारंभ स्ट्रीमिंग पर स्किप होने का जोखिम बढ़ाता है और रील्स/टिकटॉक/शॉर्ट्स के लिए अच्छा क्लिप नहीं बनता।",
    },
    ("hook_repetition_score", "below_ideal"): {
        "en": "The track doesn't return to a strongly recognizable repeated idea (hook/chorus) as much as typical hits — consider tightening the chorus so it's more instantly identifiable and repeats more clearly.",
        "ne": "यो गीत सामान्य हिटहरूजस्तो बलियो र चिनिने दोहोरिने भाग (हुक/कोरस) मा फर्किंदैन — कोरसलाई अझ तुरुन्तै चिनिने र स्पष्ट रूपमा दोहोरिने बनाउनुहोस्।",
        "hi": "यह गाना सामान्य हिट गानों जितनी मज़बूती से पहचाने जाने वाली दोहराई गई बात (हुक/कोरस) पर वापस नहीं आता — कोरस को और तुरंत पहचाने जाने योग्य और स्पष्ट रूप से दोहराने लायक बनाने पर विचार करें।",
    },
    ("brightness", "below_ideal"): {
        "en": "Mix reads as darker/warmer than typical current hits — a touch more high-end presence (vocal clarity, cymbals/hi-hats) may help it compete in a bright modern mix landscape.",
        "ne": "मिक्स हालैका सामान्य हिटहरूभन्दा अँध्यारो/न्यानो लाग्छ — अलि बढी उच्च-फ्रिक्वेन्सी उपस्थिति (स्वरको स्पष्टता, साइम्बल्स/हाई-ह्याट) ले उज्यालो आधुनिक मिक्सको प्रतिस्पर्धामा मद्दत गर्न सक्छ।",
        "hi": "मिक्स मौजूदा सामान्य हिट गानों से अधिक गहरा/गर्म लगता है — थोड़ी और उच्च-फ़्रीक्वेंसी उपस्थिति (स्वर की स्पष्टता, साइम्बल्स/हाई-हैट) चमकीले आधुनिक मिक्स परिदृश्य में प्रतिस्पर्धा करने में मदद कर सकती है।",
    },
    ("brightness", "above_ideal"): {
        "en": "Mix reads as unusually bright/harsh — worth a listen to check it isn't fatiguing on repeated plays.",
        "ne": "मिक्स असामान्य रूपमा उज्यालो/तीखो लाग्छ — बारम्बार सुँदा थकाउने नहोस् भनी जाँच्नुहोस्।",
        "hi": "मिक्स असामान्य रूप से चमकीला/तीखा लगता है — जांच लें कि बार-बार सुनने पर यह थकाऊ न लगे।",
    },
    ("duration_sec", "above_ideal"): {
        "en": "Song runs longer than the current norm for this market — streaming-era hits have generally compressed in length; consider tightening structure (fewer repeated sections, shorter outro).",
        "ne": "गीत यस बजारको हालको सामान्य लम्बाइभन्दा लामो छ — स्ट्रिमिङ युगका हिटहरू सामान्यतया छोटा हुँदै गएका छन्; संरचना कसिलो बनाउनुहोस् (कम दोहोरिने खण्ड, छोटो आउट्रो)।",
        "hi": "गाना इस बाज़ार के मौजूदा मानक से लंबा है — स्ट्रीमिंग युग के हिट गाने आमतौर पर छोटे हुए हैं; संरचना को कसने पर विचार करें (कम दोहराए गए हिस्से, छोटा आउट्रो)।",
    },
    ("duration_sec", "below_ideal"): {
        "en": "Song is shorter than typical — usually fine, but make sure the hook has enough room to land and repeat before the track ends.",
        "ne": "गीत सामान्यभन्दा छोटो छ — प्रायः ठिकै हुन्छ, तर हुकलाई असर पार्न र दोहोरिन पर्याप्त ठाउँ छ भनी पक्का गर्नुहोस्।",
        "hi": "गाना सामान्य से छोटा है — आमतौर पर ठीक है, लेकिन सुनिश्चित करें कि हुक को असर डालने और दोहराने के लिए पर्याप्त जगह मिले।",
    },
}


def feature_suggestion(feature: str, status: str, lang: str) -> str | None:
    entry = FEATURE_SUGGESTIONS.get((feature, status))
    if not entry:
        return None
    return _pick(entry, lang)


# ---------------------------------------------------------------------------
# Mode (major/minor) note
# ---------------------------------------------------------------------------

_MODE_NOTE_TEMPLATE = {
    "en": "Key/mode: {key} {mode} — pop hits have trended slightly toward minor keys over the long run, but this is a weak signal on its own; not a reason to change a song that otherwise works.",
    "ne": "स्वर/मोड: {key} {mode} — लामो समयमा पप हिटहरू अलि माइनर स्वरतिर झुकेका छन्, तर यो आफैंमा कमजोर सङ्केत हो; अन्यथा राम्रो चलिरहेको गीत बदल्नुपर्ने कारण होइन।",
    "hi": "स्वर/मोड: {key} {mode} — लंबे समय में पॉप हिट गानों का रुझान थोड़ा माइनर स्वर की ओर रहा है, लेकिन यह अपने आप में एक कमज़ोर संकेत है; इसे बदलने का कारण न मानें अगर गाना अन्यथा अच्छा काम कर रहा है।",
}

_MODE_LABEL = {
    "major": {"en": "major", "ne": "मेजर", "hi": "मेजर"},
    "minor": {"en": "minor", "ne": "माइनर", "hi": "माइनर"},
}


def mode_note(key: str, mode: str, lang: str) -> str:
    mode_label = _pick(_MODE_LABEL.get(mode, {"en": mode}), lang)
    return _pick(_MODE_NOTE_TEMPLATE, lang).format(key=key, mode=mode_label)


# ---------------------------------------------------------------------------
# Theme labels + lyrics-related suggestions
# ---------------------------------------------------------------------------

THEME_LABELS = {
    "romance":               {"en": "romance", "ne": "प्रेम/रोमान्स", "hi": "रोमांस"},
    "heartbreak_separation": {"en": "heartbreak/separation", "ne": "बिछोड/पीडा", "hi": "जुदाई/दर्द"},
    "migration_diaspora":    {"en": "migration/diaspora", "ne": "बसाइँसराइ/प्रवास", "hi": "प्रवासन/डायस्पोरा"},
    "ambition_struggle":     {"en": "ambition/struggle", "ne": "महत्वाकांक्षा/संघर्ष", "hi": "महत्वाकांक्षा/संघर्ष"},
    "celebration_party":     {"en": "celebration/party", "ne": "उत्सव/रमाइलो", "hi": "उत्सव/पार्टी"},
    "social_commentary":     {"en": "social commentary", "ne": "सामाजिक टिप्पणी", "hi": "सामाजिक टिप्पणी"},
}


def theme_label(theme: str, lang: str) -> str:
    return _pick(THEME_LABELS.get(theme, {"en": theme}), lang)


_LYRICS_THEME_MISMATCH_TEMPLATE = {
    "en": "Lyrics theme ('{theme}') doesn't strongly match the themes currently resonating in this market ({resonant}). Consider whether the story/angle can lean into one of those without forcing it.",
    "ne": "बोलको विषय ('{theme}') यस बजारमा अहिले प्रभावकारी रहेका विषयहरू ({resonant}) सँग बलियोसँग मेल खाँदैन। कथा/कोणलाई कृत्रिम नबनाई ती विषयतर्फ ढाल्न सकिन्छ कि सोच्नुहोस्।",
    "hi": "बोल का विषय ('{theme}') इस बाज़ार में अभी असरदार साबित हो रहे विषयों ({resonant}) से मेल नहीं खाता। बिना ज़बरदस्ती किए कहानी/नज़रिये को उनमें से किसी एक की ओर मोड़ा जा सकता है या नहीं, इस पर विचार करें।",
}

_LYRICS_CODE_SWITCH_TEMPLATE = {
    "en": "This market has shown strong resonance with bilingual/code-switched lyrics (e.g. Nepali-English). Consider whether a natural code-switch fits the song's voice.",
    "ne": "यस बजारमा दुई भाषा मिसिएका (जस्तै नेपाली-अङ्ग्रेजी) बोलले राम्रो प्रतिक्रिया पाएको देखिन्छ। गीतको शैलीमा स्वाभाविक भाषा-मिश्रण मिल्छ कि सोच्नुहोस्।",
    "hi": "इस बाज़ार में दो भाषाओं के मेल वाले (जैसे नेपाली-अंग्रेज़ी) बोल को अच्छी प्रतिक्रिया मिलती देखी गई है। गाने की शैली में स्वाभाविक भाषा-मिश्रण उचित है या नहीं, इस पर विचार करें।",
}


def lyrics_theme_mismatch_suggestion(theme: str | None, resonant_themes: list, lang: str) -> str:
    theme_text = theme_label(theme, lang) if theme else {"en": "unclear", "ne": "अस्पष्ट", "hi": "अस्पष्ट"}[lang]
    resonant_text = ", ".join(theme_label(t, lang) for t in sorted(resonant_themes))
    return _pick(_LYRICS_THEME_MISMATCH_TEMPLATE, lang).format(theme=theme_text, resonant=resonant_text)


def lyrics_code_switch_suggestion(lang: str) -> str:
    return _pick(_LYRICS_CODE_SWITCH_TEMPLATE, lang)


# ---------------------------------------------------------------------------
# Sentiment labels
# ---------------------------------------------------------------------------

SENTIMENT_LABELS = {
    "positive": {"en": "positive", "ne": "सकारात्मक", "hi": "सकारात्मक"},
    "negative": {"en": "negative", "ne": "नकारात्मक", "hi": "नकारात्मक"},
    "mixed":    {"en": "mixed", "ne": "मिश्रित", "hi": "मिश्रित"},
    "neutral":  {"en": "neutral", "ne": "तटस्थ", "hi": "तटस्थ"},
}


def sentiment_label(label: str | None, lang: str) -> str:
    if not label:
        return {"en": "none detected", "ne": "पत्ता लागेन", "hi": "कुछ नहीं मिला"}[lang]
    return _pick(SENTIMENT_LABELS.get(label, {"en": label}), lang)


# ---------------------------------------------------------------------------
# Caveats (fixed keys)
# ---------------------------------------------------------------------------

CAVEATS = {
    "fit_not_probability": {
        "en": "This score reflects fit against RECENT songs' measurable audio/lyrics patterns for the chosen market — it is not a 'probability of becoming a hit.'",
        "ne": "यो स्कोरले छानिएको बजारका हालैका गीतहरूको मापनयोग्य अडियो/बोल ढाँचासँगको मेल देखाउँछ — यो 'हिट हुने सम्भावना' होइन।",
        "hi": "यह स्कोर चुने गए बाज़ार के हालिया गानों के मापने योग्य ऑडियो/बोल पैटर्न से मेल दर्शाता है — यह 'हिट होने की संभावना' नहीं है।",
    },
    "non_audio_factors": {
        "en": "Non-audio factors the research consistently found decisive — artist fame, marketing budget, a viral choreography/influencer moment, release timing relative to festivals — are NOT measured here and can outweigh everything above.",
        "ne": "अनुसन्धानले बारम्बार महत्त्वपूर्ण देखाएका गैर-अडियो कारकहरू — कलाकारको प्रसिद्धि, मार्केटिङ बजेट, भाइरल कोरियोग्राफी/इन्फ्लुएन्सर क्षण, चाडपर्वसँग मिलाइएको रिलिज समय — यहाँ मापन गरिएको छैन र यी माथिका सबै कुरालाई भारी पर्न सक्छन्।",
        "hi": "शोध में बार-बार महत्वपूर्ण पाए गए गैर-ऑडियो कारक — कलाकार की प्रसिद्धि, मार्केटिंग बजट, वायरल कोरियोग्राफी/इन्फ्लुएंसर पल, त्योहारों के अनुसार रिलीज़ का समय — यहाँ मापे नहीं गए हैं और ऊपर की हर बात पर भारी पड़ सकते हैं।",
    },
    "heuristic_reference": {
        "en": "The reference ranges used for this market are heuristic starting points from the Phase 1 research report, not fitted from a large labeled dataset — treat this as a directional read, not a certified prediction.",
        "ne": "यस बजारका लागि प्रयोग गरिएका सन्दर्भ दायराहरू पहिलो चरणको अनुसन्धान प्रतिवेदनबाट लिइएका सुरुवाती अनुमान हुन्, ठूलो लेबल गरिएको डेटासेटबाट होइन — यसलाई दिशासूचक मात्र मान्नुहोस्, प्रमाणित भविष्यवाणी होइन।",
        "hi": "इस बाज़ार के लिए इस्तेमाल की गई संदर्भ सीमाएँ पहले चरण की शोध रिपोर्ट से लिए गए शुरुआती अनुमान हैं, किसी बड़े लेबल किए गए डेटासेट से नहीं — इसे केवल दिशा-सूचक समझें, प्रमाणित भविष्यवाणी नहीं।",
    },
    "no_lyrics": {
        "en": "No lyrics were analyzed (none provided and transcription unavailable/failed) — the score is audio-only.",
        "ne": "कुनै बोल विश्लेषण गरिएन (कुनै बोल दिइएन र ट्रान्सक्रिप्सन उपलब्ध/सफल भएन) — स्कोर अडियोमा मात्र आधारित छ।",
        "hi": "कोई बोल विश्लेषित नहीं किए गए (न तो कोई बोल दिए गए और न ही ट्रांसक्रिप्शन उपलब्ध/सफल हुआ) — स्कोर केवल ऑडियो पर आधारित है।",
    },
}


def caveat_text(key: str, lang: str) -> str:
    return _pick(CAVEATS.get(key, {"en": key}), lang)


# ---------------------------------------------------------------------------
# General UI strings (for app.py / cli.py)
# ---------------------------------------------------------------------------

UI = {
    "app_title":            {"en": "Hit Song Predictor", "ne": "हिट गीत भविष्यवाणी", "hi": "हिट गीत भविष्यवाणी"},
    "app_caption":          {
        "en": "Upload a song and get a fit score against recent Nepali / Indian market trends, with a feature-by-feature breakdown and suggestions. This is a directional tool, not a guarantee.",
        "ne": "गीत अपलोड गर्नुहोस् र हालैका नेपाली/भारतीय बजार प्रवृत्तिसँगको उपयुक्तता स्कोर, विशेषता-अनुसारको विवरण, र सुझावहरू पाउनुहोस्। यो दिशासूचक उपकरण हो, ग्यारेन्टी होइन।",
        "hi": "गाना अपलोड करें और हालिया नेपाली/भारतीय बाज़ार रुझानों के मुक़ाबले उपयुक्तता स्कोर, फ़ीचर-दर-फ़ीचर विवरण और सुझाव पाएं। यह एक दिशा-सूचक उपकरण है, गारंटी नहीं।",
    },
    "language":              {"en": "Language", "ne": "भाषा", "hi": "भाषा"},
    "settings":              {"en": "Settings", "ne": "सेटिङहरू", "hi": "सेटिंग्स"},
    "target_market":         {"en": "Target market", "ne": "लक्षित बजार", "hi": "लक्षित बाज़ार"},
    "lyrics_optional":       {"en": "Lyrics (optional)", "ne": "बोल (वैकल्पिक)", "hi": "बोल (वैकल्पिक)"},
    "lyrics_mode_question":  {"en": "How do you want to provide lyrics?", "ne": "तपाईं बोल कसरी दिन चाहनुहुन्छ?", "hi": "आप बोल कैसे देना चाहते हैं?"},
    "lyrics_mode_paste":     {"en": "Paste text", "ne": "पाठ टाँस्नुहोस्", "hi": "टेक्स्ट पेस्ट करें"},
    "lyrics_mode_upload":    {"en": "Upload .txt file", "ne": ".txt फाइल अपलोड गर्नुहोस्", "hi": ".txt फ़ाइल अपलोड करें"},
    "lyrics_mode_transcribe":{"en": "Try auto-transcribe from audio", "ne": "अडियोबाट स्वतः ट्रान्सक्राइब गर्ने प्रयास गर्नुहोस्", "hi": "ऑडियो से स्वतः ट्रांसक्राइब करने का प्रयास करें"},
    "lyrics_mode_skip":      {"en": "Skip lyrics", "ne": "बोल छोड्नुहोस्", "hi": "बोल छोड़ें"},
    "paste_lyrics_label":    {"en": "Paste lyrics here (any language/mix)", "ne": "यहाँ बोल टाँस्नुहोस् (जुनसुकै भाषा/मिश्रण)", "hi": "यहाँ बोल पेस्ट करें (किसी भी भाषा/मिश्रण में)"},
    "lyrics_file_label":     {"en": "Lyrics .txt file", "ne": "बोलको .txt फाइल", "hi": "बोल की .txt फ़ाइल"},
    "whisper_lang_label":    {"en": "Hint the language for transcription (optional, improves accuracy)", "ne": "ट्रान्सक्रिप्सनका लागि भाषा संकेत गर्नुहोस् (वैकल्पिक, शुद्धता बढाउँछ)", "hi": "ट्रांसक्रिप्शन के लिए भाषा का संकेत दें (वैकल्पिक, सटीकता बढ़ाता है)"},
    "whisper_caption":       {
        "en": "Requires the optional Whisper package (see requirements-optional.txt). If it's not installed, this will fall back to audio-only analysis.",
        "ne": "यसका लागि वैकल्पिक Whisper प्याकेज चाहिन्छ (requirements-optional.txt हेर्नुहोस्)। इन्स्टल नभएमा, अडियो-मात्र विश्लेषणमा फर्किन्छ।",
        "hi": "इसके लिए वैकल्पिक Whisper पैकेज चाहिए (requirements-optional.txt देखें)। इंस्टॉल न होने पर, यह केवल-ऑडियो विश्लेषण पर वापस चला जाएगा।",
    },
    "reference_caption":     {
        "en": "Reference ranges are heuristic starting points from the Phase 1 research report — not fitted from a large labeled dataset.",
        "ne": "सन्दर्भ दायराहरू पहिलो चरणको अनुसन्धान प्रतिवेदनबाट लिइएका सुरुवाती अनुमान हुन् — ठूलो लेबल गरिएको डेटासेटबाट होइन।",
        "hi": "संदर्भ सीमाएँ पहले चरण की शोध रिपोर्ट से लिए गए शुरुआती अनुमान हैं — किसी बड़े लेबल किए गए डेटासेट से नहीं।",
    },
    "upload_label":          {"en": "Upload a song (mp3, wav, m4a, flac)", "ne": "गीत अपलोड गर्नुहोस् (mp3, wav, m4a, flac)", "hi": "गाना अपलोड करें (mp3, wav, m4a, flac)"},
    "analyze_button":        {"en": "Analyze", "ne": "विश्लेषण गर्नुहोस्", "hi": "विश्लेषण करें"},
    "upload_prompt":         {"en": "Upload a song above to get started.", "ne": "सुरु गर्न माथि गीत अपलोड गर्नुहोस्।", "hi": "शुरू करने के लिए ऊपर गाना अपलोड करें।"},
    "analyzing":             {"en": "Analyzing audio (and lyrics, if provided)... this can take a minute for longer files.", "ne": "अडियो (र बोल, दिइएको भए) विश्लेषण गर्दै... लामो फाइलका लागि एक मिनेटसम्म लाग्न सक्छ।", "hi": "ऑडियो (और बोल, यदि दिए गए हों) का विश्लेषण हो रहा है... लंबी फ़ाइलों के लिए एक मिनट तक लग सकता है।"},
    "analysis_failed":       {"en": "Analysis failed: {error}", "ne": "विश्लेषण असफल भयो: {error}", "hi": "विश्लेषण विफल: {error}"},
    "fit_score_prefix":      {"en": "Fit score", "ne": "उपयुक्तता स्कोर", "hi": "उपयुक्तता स्कोर"},
    "audio_only_subscore":   {"en": "Audio-only sub-score: {score:.1f} / 100", "ne": "अडियो-मात्र उप-स्कोर: {score:.1f} / १००", "hi": "ऑडियो-केवल उप-स्कोर: {score:.1f} / 100"},
    "lyrics_subscore":       {"en": "Lyrics sub-score: {score:.1f} / 100", "ne": "बोल उप-स्कोर: {score:.1f} / १००", "hi": "बोल उप-स्कोर: {score:.1f} / 100"},
    "suggestions_header":    {"en": "Suggestions", "ne": "सुझावहरू", "hi": "सुझाव"},
    "no_suggestions":        {"en": "No major gaps flagged against this market's recent patterns.", "ne": "यस बजारको हालैको ढाँचाविरुद्ध कुनै ठूलो कमी फेला परेन।", "hi": "इस बाज़ार के हालिया रुझानों के मुक़ाबले कोई बड़ी कमी नहीं मिली।"},
    "feature_breakdown_header": {"en": "Feature breakdown", "ne": "विशेषता विवरण", "hi": "फ़ीचर विवरण"},
    "col_feature":           {"en": "Feature", "ne": "विशेषता", "hi": "विशेषता"},
    "col_value":             {"en": "Value", "ne": "मान", "hi": "मान"},
    "col_range":             {"en": "Typical range", "ne": "सामान्य दायरा", "hi": "सामान्य सीमा"},
    "col_score":             {"en": "Score", "ne": "स्कोर", "hi": "स्कोर"},
    "col_status":            {"en": "Status", "ne": "स्थिति", "hi": "स्थिति"},
    "lyrics_analysis_header":{"en": "Lyrics analysis", "ne": "बोल विश्लेषण", "hi": "बोल विश्लेषण"},
    "lyrics_source":         {"en": "Source", "ne": "स्रोत", "hi": "स्रोत"},
    "lyrics_dominant_theme": {"en": "Dominant theme", "ne": "प्रमुख विषय", "hi": "प्रमुख विषय"},
    "lyrics_theme_match":    {"en": "Theme match with market", "ne": "बजारसँग विषय मेल", "hi": "बाज़ार से विषय मेल"},
    "lyrics_code_switch":    {"en": "Code-switch score", "ne": "भाषा-मिश्रण स्कोर", "hi": "भाषा-मिश्रण स्कोर"},
    "lyrics_sentiment":      {"en": "Sentiment", "ne": "भावना", "hi": "भावना"},
    "lyrics_sentiment_method": {"en": "Sentiment method", "ne": "भावना पत्ता लगाउने विधि", "hi": "भावना पहचान विधि"},
    "lyrics_word_count":     {"en": "Word count", "ne": "शब्द संख्या", "hi": "शब्द गणना"},
    "no_theme_detected":     {"en": "none detected", "ne": "पत्ता लागेन", "hi": "कुछ नहीं मिला"},
    "no_lyrics_analyzed":    {"en": "No lyrics were analyzed — score is audio-only.", "ne": "कुनै बोल विश्लेषण गरिएन — स्कोर अडियोमा मात्र आधारित छ।", "hi": "कोई बोल विश्लेषित नहीं किए गए — स्कोर केवल ऑडियो पर आधारित है।"},
    "raw_features_expander": {"en": "Raw extracted audio features", "ne": "कच्चा निकालिएका अडियो विशेषताहरू", "hi": "कच्ची निकाली गई ऑडियो विशेषताएँ"},
    "theme_scores_expander": {"en": "Theme scores (raw)", "ne": "विषय स्कोर (कच्चा)", "hi": "विषय स्कोर (कच्चा)"},
    "caveats_header":        {"en": "⚠️ Read before you trust this score", "ne": "⚠️ यो स्कोरलाई विश्वास गर्नुअघि पढ्नुहोस्", "hi": "⚠️ इस स्कोर पर भरोसा करने से पहले पढ़ें"},
}


def ui(key: str, lang: str, **kwargs) -> str:
    text = _pick(UI.get(key, {"en": key}), lang)
    if kwargs:
        return text.format(**kwargs)
    return text


# ---------------------------------------------------------------------------
# Market display labels (optional localized display names; the underlying
# market KEY and the canonical English "label" in reference_profiles.json
# stay the source of truth)
# ---------------------------------------------------------------------------

MARKET_LABELS = {
    "nepali_pop": {
        "en": "Nepali Pop / Folk-Fusion (recent, ~2024-2026)",
        "ne": "नेपाली पप / लोक-फ्युजन (हालैको, ~२०२४-२०२६)",
        "hi": "नेपाली पॉप / लोक-फ्यूज़न (हालिया, ~2024-2026)",
    },
    "bollywood_hindi": {
        "en": "Bollywood / Hindi Pop (recent, ~2024-2026)",
        "ne": "बलिउड / हिन्दी पप (हालैको, ~२०२४-२०२६)",
        "hi": "बॉलीवुड / हिंदी पॉप (हालिया, ~2024-2026)",
    },
    "punjabi_crossover": {
        "en": "Punjabi / Punjabi-Bollywood Crossover (recent, ~2024-2026)",
        "ne": "पञ्जाबी / पञ्जाबी-बलिउड क्रसओभर (हालैको, ~२०२४-२०२६)",
        "hi": "पंजाबी / पंजाबी-बॉलीवुड क्रॉसओवर (हालिया, ~2024-2026)",
    },
    "generic_south_asian_pop": {
        "en": "Generic / Unsure Market (wide fallback ranges)",
        "ne": "सामान्य / अनिश्चित बजार (फराकिलो दायरा)",
        "hi": "सामान्य / अनिश्चित बाज़ार (व्यापक सीमा)",
    },
}


def market_label(market_key: str, lang: str, fallback: str = "") -> str:
    entry = MARKET_LABELS.get(market_key)
    if not entry:
        return fallback or market_key
    return _pick(entry, lang)


# ---------------------------------------------------------------------------
# render_result — turns a language-agnostic scoring result (see
# engine/scoring.compute_score, merged with pipeline.analyze_song's extras)
# into a fully localized dict ready for app.py / cli.py to display.
# ---------------------------------------------------------------------------

def render_result(result: dict, lang: str) -> dict:
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    breakdown = []
    for row in result["audio_breakdown"]:
        breakdown.append({
            **row,
            "label": feature_label(row["feature"], lang),
            "status_label": _pick(STATUS_LABELS.get(row["status"], {}), lang),
            "comment": feature_comment(
                row["feature"], row["value"], row["status"],
                row["ideal_low"], row["ideal_high"], lang,
            ),
        })

    mode_note_text = None
    if result.get("mode_info"):
        mi = result["mode_info"]
        mode_note_text = mode_note(mi["key"], mi["mode"], lang)

    suggestions = []
    for trig in result.get("suggestion_triggers", []):
        if trig["type"] == "feature":
            text = feature_suggestion(trig["feature"], trig["status"], lang)
        elif trig["type"] == "lyrics_theme_mismatch":
            text = lyrics_theme_mismatch_suggestion(trig["theme"], trig["resonant_themes"], lang)
        elif trig["type"] == "lyrics_code_switch":
            text = lyrics_code_switch_suggestion(lang)
        else:
            text = None
        if text:
            suggestions.append(text)

    caveats = [caveat_text(k, lang) for k in result.get("caveat_keys", [])]

    lyrics_out = {"available": False}
    lyr = result.get("lyrics", {})
    if lyr.get("available"):
        theme_scores_labeled = {
            theme_label(k, lang): v for k, v in lyr.get("theme_scores", {}).items()
        }
        lyrics_out = {
            **lyr,
            "dominant_theme_label": theme_label(lyr["dominant_theme"], lang) if lyr.get("dominant_theme") else ui("no_theme_detected", lang),
            "theme_scores_labeled": theme_scores_labeled,
            "sentiment_label_localized": sentiment_label(lyr.get("sentiment_label"), lang),
        }

    market_key = result.get("market_key", "")
    localized_market_label = market_label(market_key, lang, fallback=result.get("market_label", market_key))

    return {
        "lang": lang,
        "overall_score_100": result["overall_score_100"],
        "audio_score_100": result["audio_score_100"],
        "market_key": market_key,
        "market_label": localized_market_label,
        "breakdown": breakdown,
        "mode_note": mode_note_text,
        "lyrics": lyrics_out,
        "suggestions": suggestions,
        "caveats": caveats,
        "audio_features": result.get("audio_features"),
        "lyrics_features": result.get("lyrics_features"),
    }
