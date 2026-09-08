"""
audio_features.py
------------------
Extracts a set of measurable, DSP-based features from an audio file using librosa.

IMPORTANT — read this before trusting the numbers:
This module computes REASONABLE PROXIES for the concepts discussed in the Phase 1
research report (danceability, energy, acousticness, "hookiness", intro length, etc.),
not the exact proprietary algorithms Spotify or any label uses. Spotify's own
"audio features" API was restricted for new developer apps in Nov 2024, so there is
no free, official ground truth to calibrate against — these proxies are built from
first principles (tempo/beat analysis, spectral analysis, harmonic-percussive
separation, self-similarity) using open-source signal processing. Treat every score
here as "a reasonable engineering approximation", not a lab-certified measurement.

All functions are defensive: if a particular sub-computation fails (e.g. on a very
short or very quiet clip), it falls back to a safe default rather than crashing the
whole extraction.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np
import librosa

try:
    import pyloudnorm as pyln
    _HAS_PYLOUDNORM = True
except ImportError:  # pragma: no cover
    _HAS_PYLOUDNORM = False

warnings.filterwarnings("ignore", category=UserWarning, module="librosa")

SR = 22050  # analysis sample rate — plenty for the features we compute
EPS = 1e-9

# Krumhansl-Kessler major/minor key profiles (classic key-finding templates)
_MAJOR_PROFILE = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
)
_MINOR_PROFILE = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
)
_PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


@dataclass
class AudioFeatures:
    duration_sec: float
    tempo_bpm: float
    beat_strength: float          # 0-1, how regular the beat grid is (rhythmic stability)
    danceability_proxy: float     # 0-1, combines beat regularity + pulse clarity
    energy: float                 # 0-1, normalized RMS energy
    loudness_lufs: Optional[float]  # integrated loudness in LUFS (None if pyloudnorm unavailable)
    dynamic_range_db: float       # spread between loud and quiet sections
    brightness: float             # 0-1, normalized spectral centroid ("crispness")
    acousticness_proxy: float     # 0-1, higher = more acoustic/raw-sounding
    speechiness_proxy: float      # 0-1, higher = more talk-like / noisy vocal delivery
    key: str                      # estimated musical key, e.g. "C#"
    mode: str                     # "major" or "minor"
    key_confidence: float         # 0-1, how confident the key/mode estimate is
    intro_length_sec: float       # approx. seconds before the track "gets going"
    hook_repetition_score: float  # 0-1, how much the track repeats a recognizable section
    section_estimate: int         # rough count of structurally distinct sections

    def to_dict(self) -> dict:
        return asdict(self)


def _safe(fn, default):
    try:
        return fn()
    except Exception:
        return default


def extract_audio_features(path: str) -> AudioFeatures:
    """Load an audio file and compute the full feature set. Raises only if the
    file genuinely cannot be loaded/decoded at all."""
    y, sr = librosa.load(path, sr=SR, mono=True)
    if y.size == 0:
        raise ValueError("Decoded audio is empty — the file may be corrupt or silent.")

    duration_sec = float(librosa.get_duration(y=y, sr=sr))

    # --- Rhythm ---------------------------------------------------------
    tempo_bpm, beat_strength = _tempo_and_beat_strength(y, sr)
    danceability_proxy = _danceability(y, sr, beat_strength)

    # --- Energy / loudness / dynamics -----------------------------------
    rms = librosa.feature.rms(y=y)[0]
    energy = float(np.clip(np.mean(rms) / 0.15, 0.0, 1.0))
    loudness_lufs = _integrated_loudness(y, sr)
    db = 20.0 * np.log10(rms + EPS)
    dynamic_range_db = float(np.percentile(db, 95) - np.percentile(db, 5))

    # --- Timbre / production ---------------------------------------------
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    brightness = float(np.clip(np.mean(centroid) / 4000.0, 0.0, 1.0))

    y_harm, y_perc = _safe(lambda: librosa.effects.hpss(y), (y, np.zeros_like(y)))
    harm_energy = float(np.sum(y_harm ** 2))
    perc_energy = float(np.sum(y_perc ** 2))
    acousticness_proxy = float(np.clip(harm_energy / (harm_energy + perc_energy + EPS), 0.0, 1.0))

    zcr = librosa.feature.zero_crossing_rate(y)[0]
    speechiness_proxy = float(np.clip(np.mean(zcr) / 0.15, 0.0, 1.0))

    # --- Harmony (key / mode) --------------------------------------------
    key, mode, key_confidence = _estimate_key(y_harm, sr)

    # --- Structure ---------------------------------------------------------
    intro_length_sec = _estimate_intro_length(rms, sr, hop_length=512)
    hook_repetition_score, section_estimate = _estimate_structure(y, sr)

    return AudioFeatures(
        duration_sec=round(duration_sec, 2),
        tempo_bpm=round(float(tempo_bpm), 1),
        beat_strength=round(beat_strength, 3),
        danceability_proxy=round(danceability_proxy, 3),
        energy=round(energy, 3),
        loudness_lufs=round(loudness_lufs, 2) if loudness_lufs is not None else None,
        dynamic_range_db=round(dynamic_range_db, 2),
        brightness=round(brightness, 3),
        acousticness_proxy=round(acousticness_proxy, 3),
        speechiness_proxy=round(speechiness_proxy, 3),
        key=key,
        mode=mode,
        key_confidence=round(key_confidence, 3),
        intro_length_sec=round(intro_length_sec, 2),
        hook_repetition_score=round(hook_repetition_score, 3),
        section_estimate=section_estimate,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _tempo_and_beat_strength(y, sr):
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
    tempo = float(np.atleast_1d(tempo)[0])
    if len(beats) < 4:
        return tempo, 0.3  # not enough beats detected to judge regularity — assume weak
    beat_times = librosa.frames_to_time(beats, sr=sr)
    intervals = np.diff(beat_times)
    if len(intervals) == 0 or np.mean(intervals) == 0:
        return tempo, 0.3
    regularity = 1.0 - float(np.std(intervals) / (np.mean(intervals) + EPS))
    return tempo, float(np.clip(regularity, 0.0, 1.0))


def _danceability(y, sr, beat_strength):
    def _pulse_clarity():
        tempogram = librosa.feature.tempogram(y=y, sr=sr)
        peak = np.mean(np.max(tempogram, axis=0))
        mean = np.mean(tempogram) + EPS
        return float(np.clip((peak / mean) / 8.0, 0.0, 1.0))

    pulse_clarity = _safe(_pulse_clarity, beat_strength)
    return float(np.clip(0.5 * beat_strength + 0.5 * pulse_clarity, 0.0, 1.0))


def _integrated_loudness(y, sr):
    if not _HAS_PYLOUDNORM:
        return None

    def _measure():
        meter = pyln.Meter(sr)
        loudness = meter.integrated_loudness(y.astype(np.float64))
        if loudness == float("-inf") or np.isnan(loudness):
            return None
        return float(loudness)

    return _safe(_measure, None)


def _estimate_key(y_harm, sr):
    def _compute():
        chroma = librosa.feature.chroma_cqt(y=y_harm, sr=sr)
        chroma_mean = chroma.mean(axis=1)
        if np.sum(chroma_mean) == 0:
            return "Unknown", "unknown", 0.0

        best_score, best_key, best_mode = -np.inf, "C", "major"
        scores = []
        for i in range(12):
            major_score = np.corrcoef(np.roll(_MAJOR_PROFILE, i), chroma_mean)[0, 1]
            minor_score = np.corrcoef(np.roll(_MINOR_PROFILE, i), chroma_mean)[0, 1]
            scores.append(major_score)
            scores.append(minor_score)
            if major_score > best_score:
                best_score, best_key, best_mode = major_score, _PITCH_CLASSES[i], "major"
            if minor_score > best_score:
                best_score, best_key, best_mode = minor_score, _PITCH_CLASSES[i], "minor"

        scores = sorted(scores, reverse=True)
        gap = scores[0] - scores[1] if len(scores) > 1 else 0.0
        confidence = float(np.clip(gap * 3.0, 0.0, 1.0))
        return best_key, best_mode, confidence

    return _safe(_compute, ("Unknown", "unknown", 0.0))


def _estimate_intro_length(rms, sr, hop_length):
    """Approximates how long it takes for the track to 'get going' by finding
    the first point where energy sustainably exceeds a threshold relative to
    the track's own median. This is a proxy for 'time before vocal/hook enters'
    — it cannot distinguish an instrumental build-up from an actual vocal
    entrance without a vocal-separation model (a documented future upgrade;
    see README)."""
    if len(rms) < 5:
        return 0.0
    threshold = 0.5 * float(np.median(rms))
    sustained_needed = max(1, int(round(1.0 * sr / hop_length)))  # ~1 second sustained
    above = rms > threshold
    run = 0
    for i, flag in enumerate(above):
        run = run + 1 if flag else 0
        if run >= sustained_needed:
            first_frame = i - sustained_needed + 1
            return float(librosa.frames_to_time(first_frame, sr=sr, hop_length=hop_length))
    return 0.0


def _estimate_structure(y, sr, n_chunks=8):
    """Chunks the track and measures how similar each chunk is to the OTHER
    (non-adjacent) chunks. A high average similarity means the song keeps
    returning to a recognizable idea (a repeated hook/chorus) — a rough,
    cheap stand-in for real chorus-detection / self-similarity segmentation."""
    def _compute():
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        n_frames = mfcc.shape[1]
        if n_frames < n_chunks * 2:
            return 0.3, 1

        chunk_len = n_frames // n_chunks
        chunk_vecs = [
            mfcc[:, i * chunk_len:(i + 1) * chunk_len].mean(axis=1)
            for i in range(n_chunks)
        ]
        chunk_vecs = np.array(chunk_vecs)
        norms = np.linalg.norm(chunk_vecs, axis=1, keepdims=True) + EPS
        normed = chunk_vecs / norms
        sim = normed @ normed.T

        best_matches = []
        distinct_sections = 1
        for i in range(n_chunks):
            others = [sim[i, j] for j in range(n_chunks) if abs(i - j) > 1]
            if others:
                best_matches.append(max(others))
        hook_score = float(np.clip(np.mean(best_matches) if best_matches else 0.3, 0.0, 1.0))

        # very rough section count: cluster chunks whose mutual similarity > 0.8
        visited = set()
        clusters = 0
        for i in range(n_chunks):
            if i in visited:
                continue
            clusters += 1
            visited.add(i)
            for j in range(n_chunks):
                if sim[i, j] > 0.8:
                    visited.add(j)
        return hook_score, clusters

    return _safe(_compute, (0.3, 4))
