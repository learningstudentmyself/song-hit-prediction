# What Makes a Hit Song? A Time-Aware Analysis for Nepali & Indian Music

**Prepared for:** HitSongPrediction project
**Date:** September 2026
**Purpose:** Phase 1 deliverable — identify the elements that historically correlate with hit songs, how those elements shift by era, and translate them into a feature schema the future prediction engine can extract from an uploaded audio file or composition.

---

## 1. Executive summary

No single musical ingredient reliably makes a song a hit. Across every academic study reviewed, the strongest individual audio feature (loudness or danceability) explains only a small slice of what separates a hit from a miss — the honest conclusion researchers keep landing on is that **hits are a weighted combination of many weak signals, plus non-audio factors (artist fame, timing, marketing, and social-media virality) that audio alone cannot see.** One Spotify-based study that tried to classify Billboard hits using only audio features got 86% accuracy at rejecting non-hits but struggled to precisely confirm real hits — the authors' own conclusion was that "audio features... offer an interpretation of how a song sounds, without regard to the music trends of the year it was released." That single sentence is the thesis of this whole report: **hit-making elements are trend-relative, not fixed.** A tempo, structure, or theme that guarantees a hit in one era can sound dated five years later.

This report has four parts:

- **Part 2** — the audio/lyrical/structural features that data science research finds correlated with popularity, industry-agnostic.
- **Part 3** — how Nepali music's hit-making formula has moved decade by decade, and what's working right now (2024–2026).
- **Part 4** — the same for Indian/Bollywood and the broader Hindi/Punjabi-pop ecosystem, including the regional-language boom.
- **Part 5** — a proposed feature schema and design principles for the Phase 2 prediction + suggestion engine, translating all of the above into things that can actually be computed from an uploaded audio file.

---

## 2. Universal, data-driven hit factors

### 2.1 What audio features correlate with popularity

Multiple independent studies (Spotify-feature datasets, Billboard-vs-random-track classifiers, and cross-genre analyses of 90,000+ tracks) converge on a consistent pattern:

| Feature | Direction in hits | Strength of effect |
|---|---|---|
| **Danceability** | Higher danceability tracks skew toward higher popularity — described in one 90k-track study as "the strongest audio predictor of commercial appeal," rising from ~0.55 in low-popularity tracks to ~0.66 in the highest tier | Moderate-strong, most consistent single feature |
| **Energy** | Medium-to-high energy shows up disproportionately in popular tracks (fits party/workout listening contexts) | Moderate |
| **Loudness** | Louder, more "polished" masters (closer to 0 dB) correlate with popularity — the clearest pattern in one large regression, though the correlation coefficient was still tiny (~+0.05) | Weak but consistent |
| **Acousticness** | Hits skew *less* acoustic — produced/processed sound tends to outperform raw/organic recordings | Weak-moderate |
| **Valence (mood)** | Surprisingly weak — hits appear across the full range from sad ballads to euphoric anthems. Mood alone doesn't predict success | Negligible |
| **Speechiness** | Very talk-heavy tracks underperform — hurts replayability | Weak, negative |
| **Explicit content** | One PCA-based hit-classifier found explicit rating carried the *highest variance* of any feature, though direction is genre-dependent (helps in hip-hop, penalizes mainstream pop) | Context-dependent, high variance |
| **Key/mode (major vs. minor)** | Long-run analyses of pop charts show a real historical drift toward more minor-key hits since the 1960s, but mode alone is a weak standalone predictor — it interacts with genre and era | Weak, era-dependent |

The meta-finding that matters most for engine design: **"No single audio feature strongly explains popularity."** Random Forest classifiers built purely on Spotify-style audio features can reach ~86% accuracy separating hits from a random sample, but that accuracy comes from combining ~10 features (via PCA) — not from any one dial. This means a credible engine has to score a *bundle* of features, not rank songs on any single number like "danceability."

### 2.2 Structure and pacing: the skip-rate era rewired songwriting

Streaming and short-form video have measurably changed song architecture, independent of genre:

- **Intros have collapsed.** Average instrumental intro length fell from roughly 20+ seconds in the mid-1980s to under 5 seconds by the mid-2010s. Modern hits open on vocals or the hook almost immediately.
- **The first 3–5 seconds now function as the ad for the whole song.** Roughly a quarter of streams are abandoned within the first 5 seconds, so the "hook" — the most repeatable, recognizable musical or lyrical moment — increasingly opens the track instead of arriving after a verse and pre-chorus.
- **Songs overall are trending shorter**, compressing verse-chorus cycles and cutting instrumental bridges, though this trend is genre-dependent (electronic/dance genres still run long; pop and hip-hop have compressed the most).
- **A hook designed to loop cleanly** (for short-form video reuse) now doubles as a structural songwriting goal, not just a marketing afterthought — because the same 15–30 second clip has to work as a skip-proof opening on streaming *and* a shareable loop on TikTok/Reels/Shorts.

### 2.3 Lyrics: typicality helps longevity, not peak

NLP research on lyrics (British top-40 chart data) found that songs with more "typical" lyrics for their genre/era — measured across repetition, vocabulary complexity, theme, and emotional tone — stay in the top ranks *longer*, but typicality does **not** predict how high a song peaks or how fast it climbs. In other words: familiar, genre-conforming lyrics extend a song's shelf life once it's already popular; they don't manufacture a breakout on their own. Sentiment/theme analysis is still a useful signal, but it should be modeled as a "longevity" factor rather than a "hit or not" factor.

### 2.4 Non-audio factors research keeps flagging

Every study that tried to explain popularity from audio alone hit the same wall: artist reputation, collaboration network, release timing, and marketing/virality moments explain variance that audio features cannot. Concretely: featured-artist collaborations, an artist's existing fan base and follower count, whether a choreography or meme attached itself to the song, and release timing relative to festivals/cultural moments all show up as decisive in the industry case studies below, even when the underlying audio is unremarkable.

---

## 3. Nepali music: hit-making elements by era

### 3.1 The decade arc

| Era | Dominant sound | What made a song a hit |
|---|---|---|
| **1950s** | Radio Nepal-era *adhunik geet*, folk blended with early Bollywood influence, Western instruments introduced (Amber Gurung) | Radio reach itself was the scarce resource — being played on the only national platform |
| **1960s–70s "Golden Age"** | *Adhunik geet* — melodic, emotionally direct, romantic (Narayan Gopal, Tara Devi) | Melodic memorability + lyrics capturing personal/romantic experience resonant with urban youth culture |
| **1980s** | Western pop-influenced, more energetic performance style (Deep Shrestha) | Catchy, uptempo hooks; music video as a new visual hook alongside the audio one |
| **1990s "Pop boom"** | Cassette/CD-driven mass pop (Sugam Pokharel), FM radio + early TV | Repeatable radio/TV rotation; star-vocalist identity |
| **2000s** | Genre diversification — hip-hop/rap enters addressing social issues; fusion of traditional Nepali music with modern genres; YouTube begins democratizing distribution | Songs that fused a recognizable Nepali musical identity with a modern (often Western) genre skeleton; social commentary as a differentiator |
| **2010s "Digital revolution"** | Social media + streaming enable direct artist-to-fan reach; international collaborations become feasible | Distribution no longer bottlenecked by label/radio gatekeepers — virality and diaspora reach became achievable for independent artists |
| **2020s (current)** | Genre-plural: rap, pop, rock, folk-fusion all charting simultaneously; heavy reliance on remakes/reimagined classics | See below |

### 3.2 What's driving Nepali hits right now (2024–2026)

Recent coverage of the Nepali scene converges on five recurring drivers:

1. **Emotional authenticity over polish.** Songs addressing real lived struggles — family separation from migrant labor, addiction, heartbreak, personal ambition — consistently outperform generic themes. This is culturally specific: Nepal's large labor-migration diaspora makes "separation and reunion" a uniquely resonant theme (see the Dashain/Tihar pattern below).
2. **Visual storytelling matters as much as audio.** Nepali music is heavily YouTube-first; music videos with strong narrative or cinematography (Himalayan landscapes, live-band performance footage) measurably boost engagement, more so than in markets where audio-only streaming dominates.
3. **Reimagined classics.** A large share of recent chart activity is new productions of older, already-beloved songs — modern arrangement wrapped around a melody with pre-existing emotional equity. This lowers the "discovery risk" for listeners and labels alike.
4. **Code-switched identity (Nepali-English / Nepali-diaspora lyrics).** Tracks like Sajjan Raj Vaidya's *"Nepali Angreji"* explicitly dramatize the bilingual, cross-cultural identity many young and diaspora Nepali listeners live daily. This isn't just a lyrical gimmick — it signals authenticity to a specific, large audience segment (Nepalis abroad, second-generation diaspora) that older, Nepali-only lyrics don't reach.
5. **Seasonal/festival release windows.** Dashain and Tihar function as a predictable annual demand spike: songs about migrant workers returning home, family reunion, and separation get released ahead of the festival and gain outsized airplay (radio, TV, retail, vehicles) specifically because they're timed to and thematically matched with the cultural moment. A song's *release date relative to the festival calendar* is itself a hit factor, independent of its audio content.
6. **Rise of hip-hop/rap as a youth-identity genre.** Nepali hip-hop has grown from a niche scene into a mainstream youth movement, often carrying social/political commentary — a genre vector that didn't meaningfully chart before the 2000s–2010s.

---

## 4. Indian / Bollywood music: hit-making elements by era

### 4.1 The decade arc

| Era | Dominant sound | What made a song a hit |
|---|---|---|
| **1950s–70s** | Item songs integrated into film narrative (e.g., *Aar-Paar*), classical-influenced film scores | Songs functioned as storytelling devices — character introduction, plot advancement — success was tied to cinematic integration, not standalone replay value |
| **1990s–2000s "Remix era"** | Melodic film-song core with dance-remix versions | Danceability retrofitted onto melody-first songs; item numbers still narratively anchored |
| **2010s** | Item songs shift to pure commercial spectacle (*Munni Badnaam Hui* onward) | Choreography-first, hook-step-first — songs increasingly designed as "a five-minute commercial break" rather than plot devices; by many critics' accounts, narrative integration was effectively dead by ~2018 |
| **2020s (current)** | Genre-eclectic: R&B-tinged ballads, folk-dance fusion, Punjabi rap, Afrobeats-influenced production, electro-ghazal/qawwali fusion, all charting side by side | See below |

### 4.2 What's driving Indian/Bollywood hits right now (2024–2026)

1. **Distribution has flipped: songs break on Reels first, live on playlists after.** The defining structural shift of 2024–2025 is that virality on Instagram Reels/YouTube Shorts now *precedes* and *drives* streaming success, rather than the reverse. A song's design increasingly optimizes for a loopable 15–30 second clip over cinematic sequencing.
2. **Choreography and influencer moments can single-handedly launch a song.** Concrete case: "Tauba Tauba" (2024) became a hit substantially because of actor Vicky Kaushal's own viral choreography — the dance, not the track alone, drove discovery. This is a non-audio, social-virality factor that no audio-feature model can capture.
3. **Genre eclecticism beats a single "Bollywood formula."** 2025's top-ranked songs span R&B late-night tracks, folk-touched dance records, rap anthems, orchestral ballads, and jazz-inflected production — critics explicitly note these songs "prioritize algorithmic virality over cinematic integration." There is no longer one dominant sonic template; internal genre diversity is itself the trend.
4. **"Comfortingly familiar" wins — recreations and interpolations of past hits.** Composers reworking their own earlier hits with modern, uptempo production (rather than wholly new compositions) repeatedly charted in 2024, echoing the Nepali "reimagined classics" pattern — lower discovery risk, pre-existing emotional equity.
5. **Star power compounds streaming success.** Arijit Singh became Spotify's most-followed artist globally in 2024; Diljit Dosanjh placed nine songs on a major year-end Top 100 off the back of sold-out world tours and sustained cultural momentum. Composer/producer concentration also matters — a small number of hit-makers (e.g., Pritam, Sachin-Jigar) are attached to a disproportionate share of chart entries, meaning "who made it" carries real predictive weight independent of the audio.
6. **Punjabi music and Punjabi-pop crossover into mainstream Bollywood.** Diljit Dosanjh's global crossover (including collaborations with Latin artists) reflects a broader trend of Punjabi rhythm, language, and production aesthetics moving from a regional genre into the Hindi-pop mainstream.
7. **Regional-language and independent (I-Pop) music are the fastest-growing segment.** This is arguably the single biggest structural shift in the Indian market: regional-language royalties grew 30–120%+ year-over-year across Telugu, Marathi, Bengali, Malayalam, and Haryanvi in 2025, and independent artists now occupy roughly half of Spotify India's year-end Top 10 — rivaling film soundtracks, which used to dominate entirely. Any model trained mainly on Hindi film-song data will increasingly miss where the market is actually growing.
8. **"Restraint" is emerging as a counter-trend to maximalist production.** Multiple 2025 critical retrospectives specifically praise tracks that use mood-setting and vocal-forward restraint over bombastic arrangement — a reminder that "loud/energetic" is not a universal law, just a *frequent* correlation, and eras/subgenres can invert it.

---

## 5. Cross-cutting synthesis: why "hit elements" are time-relative

Putting Parts 2–4 together, three separate forces make hits historically:

1. **Sonic-production trends** (loudness, danceability, key/mode drift, hook placement) — these shift on a roughly 5–15 year cycle and are audio-extractable.
2. **Cultural/thematic trends** (diaspora identity, migrant-labor separation, code-switched lyrics, festival timing, genre-crossover legitimacy) — these are region- and era-specific, only partly extractable from audio (mostly from lyrics/metadata/release timing), and they change faster than the underlying music theory.
3. **Non-audio virality/industry factors** (artist fame, choreography/influencer moments, composer network, marketing timing, platform algorithm behavior) — these are *not* extractable from audio at all, and every academic study that tried to predict hits from audio alone explicitly hit this ceiling.

This has a direct implication for the prediction engine: **a model trained only on audio DSP features from an uploaded file will structurally cap out well below "real" hit prediction accuracy** — because a large share of what makes something a hit today (Reels virality, artist fame, release timing) simply isn't present in the audio signal. That's not a reason to skip building it — it's a reason to (a) score against a *time-relative* reference set of songs from the same recent window rather than all-time hits, (b) be explicit in the UI about what the model can and cannot see, and (c) treat metadata inputs (artist history, planned release date, language mix) as first-class, optional features alongside the audio analysis.

---

## 6. Proposed feature schema for the Phase 2 prediction engine

Grouped by what's realistically extractable from an **uploaded audio file or a recorded composition**, versus what needs **user-supplied metadata**.

### 6.1 Audio-extractable (via DSP libraries, e.g. `librosa`, `essentia`)

| Category | Specific features |
|---|---|
| Rhythm | Tempo (BPM), beat strength/regularity, danceability proxy (rhythmic clarity + tempo stability) |
| Energy/dynamics | RMS energy, loudness (integrated LUFS), dynamic range, spectral energy distribution |
| Timbre/production | Spectral centroid/brightness, acousticness proxy (harmonic-to-percussive ratio), "polish" (noise floor, mastering loudness) |
| Harmony | Key detection, mode (major/minor), chord-change rate, harmonic complexity |
| Structure/pacing | Intro length before first vocal/hook, section segmentation (verse/chorus/bridge boundaries via self-similarity), hook repetition count, total duration, "loopability" of the strongest 15–30s segment |
| Vocals | Speechiness/vocal-density ratio, vocal presence timeline (how early vocals enter) |

### 6.2 Lyrics-extractable (if lyrics/transcript provided or transcribed via ASR)

- Sentiment/valence trajectory across the song
- Thematic classification (romance, separation/migration, ambition, social commentary, celebration, heartbreak)
- Language-mix detection (e.g., Nepali/English code-switching, Hindi/Punjabi/English mixing) — flag as a feature given its documented resonance
- Lyric typicality score relative to genre/era reference set (repetition, vocabulary complexity)
- Explicit-content flag

### 6.3 User/metadata-supplied (optional but high-value)

- Target genre/market (Nepali vs. Hindi/Bollywood vs. Punjabi vs. regional-Indian language) — since "hit drivers" differ meaningfully by market per Parts 3–4
- Planned/actual release date, checked against festival calendar (Dashain/Tihar for Nepal; Diwali/Eid/wedding season for India) for seasonal-fit scoring
- Artist/composer track record (if known) — follower count, prior chart history
- Collaboration flag (features, choreography plans, influencer tie-in)
- Reference "comparable era" window — the engine should always compare a new song against **recent** hits (rolling 2–3 year window), not all-time hits, given how fast trends move (Section 5)

### 6.4 Model design principle

Score against a **time-windowed, market-specific reference set** (e.g., "Nepali pop, last 24 months" or "Bollywood/Punjabi crossover, last 24 months") rather than a single global model — this directly addresses the "audio features don't know what year it is" limitation researchers flagged. The output should be structured as:

- An overall **fit score** relative to the chosen reference set (not a raw "hit probability," which overclaims what audio alone can predict)
- A **feature-by-feature breakdown**: which extracted features are above/below/in-range compared to recent hits in that market+genre, in plain language (e.g., "your intro runs 14 seconds before the vocal enters — recent Nepali pop hits average under 5 seconds")
- **Actionable suggestions** derived directly from the gaps: shorten instrumental intro, raise loudness/mastering level to modern streaming norms, tighten hook repetition, consider seasonal release timing, flag if lyric theme underrepresents currently resonant themes for the chosen market
- A clear **disclaimer module**: non-audio factors (artist fame, marketing, choreography/virality moments) are outside what this tool can assess, and should be named explicitly rather than silently ignored

---

## 7. Suggested next steps (Phase 2)

1. Assemble a labeled reference dataset: metadata + (where legally obtainable) audio or audio-feature exports for recent Nepali and Indian hit vs. non-hit songs, tagged by market/genre/release date.
2. Build the audio-feature and lyrics-feature extraction pipeline (Section 6.1–6.2) in Python.
3. Build the scoring-against-reference-set logic (Section 6.4) before attempting a black-box classifier — an interpretable, comparison-based scorer is both more honest about what audio can predict and directly supports the "what makes it hit or not, and how to improve it" requirement.
4. Layer in the optional metadata inputs (Section 6.3) as the accuracy-boosting second pass.
5. Revisit this report's "current era" findings (Sections 3.2 and 4.2) roughly every 12–18 months — by design, the reference set and the thematic/production trend list should be living documents, not one-time constants.

---

## Sources

**Academic / data-science research on audio features and popularity:**
- [Predicting Popularity of Songs Based on Musical Features (Medium)](https://medium.com/inst414-data-science-tech/predicting-popularity-of-songs-based-on-musical-features-c7c6ba5af0d8)
- [Predicting danceability and song ratings using deep learning and auditory features (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12453869/)
- [What Makes a Song Popular? Predicting Hit Songs with R and Machine Learning (Medium)](https://medium.com/data-and-beyond/what-makes-a-song-popular-694dbb54f378)
- [Predicting song popularity based on Spotify's audio features: insights from Indonesian streaming users](https://www.tandfonline.com/doi/full/10.1080/23270012.2023.2239824)
- [SpotHitPy: A Study For ML-Based Song Hit Prediction Using Spotify (arXiv)](https://arxiv.org/abs/2301.07978)
- [What Makes a Hit Song? 5 Surprising Insights from Analyzing 90,000 Tracks (Medium)](https://medium.com/@arungora/what-makes-a-hit-song-5-surprising-insights-from-analyzing-90-000-tracks-fb65e5947d47)
- [Correlations between Major/Minor Mode Key Signatures and Perceived Emotions (NHSJS)](https://nhsjs.com/2025/correlations-between-major-minor-mode-key-signatures-and-perceived-emotions/)
- [Pop Music Study Shows Shift Toward Minor Key Melodies Since 1960 (HuffPost)](https://www.huffpost.com/entry/pop-music-study-minor-key_n_2122726)
- [The effect of the typicality of song lyrics on song popularity (SAGE Journals)](https://journals.sagepub.com/doi/10.1177/03057356251384301)

**Structure/pacing and virality mechanics:**
- [Pop songs are getting shorter in the era of streaming and TikTok (Washington Post)](https://www.washingtonpost.com/entertainment/interactive/2024/shorter-songs-again/)
- [Hook-First Songwriting: The 0-3 Second TikTok Window (Chartlex)](https://www.chartlex.com/blog/marketing/hook-first-songwriting-tiktok-2026)
- [Has music streaming killed the instrumental intro? (Ohio State News)](https://news.osu.edu/has-music-streaming-killed-the-instrumental-intro/)

**Nepali music industry:**
- [The Evolution of Nepali Music Over the Decades (ImNepal)](https://www.imnepal.com/evolution-nepali-music-the-decades/)
- [Evolving soundscape of Nepali music 2025 (OnlineKhabar)](https://english.onlinekhabar.com/nepali-music-kicks-off-2024.html)
- [The Meaning Behind Sajjan Raj Vaidya's "Nepali Angreji" (NepalLyrics)](https://www.nepallyrics.com/2025/04/the-meaning-behind-sajjan-raj-vaidyas.html)
- [12 songs that add color to Dashain festival (Ratopati)](https://english.ratopati.com/story/22119)
- [Beats in the Himalayas: The Rise of Nepali Hip Hop (The Diplomat)](https://thediplomat.com/2019/01/beats-in-the-himalayas-the-rise-of-nepali-hip-hop/)

**Indian / Bollywood music industry:**
- [Top 25 Bollywood Songs of 2025, Ranked (Rolling Stone India)](https://rollingstoneindia.com/top-25-bollywood-songs-of-2025-ranked/)
- [Bollywood Music in 2024: The Hits That Ruled Playlists (Hollywood Reporter India)](https://www.hollywoodreporterindia.com/features/columns/bollywood-music-in-2024-the-hits-that-ruled-playlists)
- [How Bollywood item songs have devolved, lost the plot over the years (The Federal)](https://thefederal.com/films/how-bollywood-item-songs-have-devolved-and-lost-the-plot-over-the-years-152012)
- ['Punjabi Aa Gaye Oye': 2024 was the year of Diljit Dosanjh (WION)](https://www.wionews.com/entertainment-news/punjabi-aa-gaye-oye-beaming-with-desi-pride-2024-was-the-year-of-diljit-dosanjh-8579778)
- [Spotify Report: Indian Music Goes Global as Independent and Regional Artists Surge](https://spotify.substack.com/p/spotify-report-indian-music-goes)
- [Regional music goes global: Spotify report highlights surge in Telugu, Haryanvi, Tamil and more (Business Today)](https://www.businesstoday.in/technology/news/story/regional-music-goes-global-spotify-report-highlights-surge-in-telugu-haryanvi-tamil-and-more-553198-2026-09-05)
