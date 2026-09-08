"""
Generates a small synthetic WAV file for smoke-testing the engine WITHOUT
needing any real (copyrighted) song. It's not musical — just a repeating
tone pattern with some rhythm and noise — good enough to verify the DSP
pipeline runs end-to-end without crashing.
"""
import numpy as np
import soundfile as sf

def make_test_wav(path="tests/sample_test_audio.wav", duration=30, sr=22050, bpm=120):
    t = np.linspace(0, duration, int(duration * sr), endpoint=False)
    beat_period = 60.0 / bpm
    click_env = (np.mod(t, beat_period) < 0.08).astype(np.float32)

    # A simple chord-ish tone (A minor: A3, C4, E4) that repeats with a
    # "hook" every 8 seconds so hook_repetition_score has something to find.
    freqs = [220.0, 261.63, 329.63]
    tone = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs)
    hook_mask = (np.mod(t, 8.0) < 4.0).astype(np.float32)
    melody = tone * (0.5 + 0.5 * hook_mask)

    percussive = click_env * (np.random.randn(len(t)).astype(np.float32) * 0.3)
    intro_fade = np.clip(t / 4.0, 0, 1)  # ~4s fade-in to simulate an intro

    y = (melody * 0.6 + percussive * 0.4) * intro_fade
    y = y / (np.max(np.abs(y)) + 1e-9) * 0.7
    sf.write(path, y.astype(np.float32), sr)
    return path

if __name__ == "__main__":
    p = make_test_wav()
    print(f"Wrote {p}")
