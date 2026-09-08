"""
Hit Song Predictor - analysis engine package.

This package contains everything that does NOT depend on the UI:
- audio_features.py  : DSP-based feature extraction from an audio file (librosa)
- lyrics_features.py : optional lyrics transcription + theme/sentiment/language-mix analysis
- reference_data.py  : loads the market reference profiles (data/reference_profiles.json)
- scoring.py         : compares a song's features against a reference profile and produces
                        a fit score, a feature-by-feature breakdown, and suggestions
"""
