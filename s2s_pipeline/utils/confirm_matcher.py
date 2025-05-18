"""
confirm_matcher.py
─────────────────────────────────────────────────────────
Utility functions to robustly detect affirmative / negative
user responses regardless of punctuation or extra words.
Requires   rapidfuzz >= 3.6
"""

import re
from rapidfuzz import fuzz

YES_PHRASES = [
    "yes", "yeah", "yep", "sure", "correct", "right",
    "absolutely", "affirmative", "please do", "go ahead"
]
NO_PHRASES = [
    "no", "nope", "negative", "wrong", "cancel",
    "never mind", "stop", "dont"
]

def _clean(text: str) -> str:
    """lower-case, strip punctuation & extra spaces"""
    return re.sub(r"[^\w\s]", "", text.lower()).strip()

def is_affirmative(text: str, threshold: int = 85) -> bool:
    txt = _clean(text)
    return any(fuzz.partial_ratio(txt, y) >= threshold for y in YES_PHRASES)

def is_negative(text: str, threshold: int = 85) -> bool:
    txt = _clean(text)
    return any(fuzz.partial_ratio(txt, n) >= threshold for n in NO_PHRASES)

# add at bottom of s2s_pipeline/utils/confirm_matcher.py
CANCEL_PHRASES = ["cancel", "stop", "never mind", "abort", "forget it"]
FILLER_PHRASES  = ["yes", "yeah", "sure", "okay", "ok", "right"]

def is_cancel(text: str, threshold: int = 85) -> bool:
    txt = _clean(text)
    return any(fuzz.partial_ratio(txt, c) >= threshold for c in CANCEL_PHRASES)

def looks_like_filler(text: str, threshold: int = 90) -> bool:
    txt = _clean(text)
    return any(fuzz.partial_ratio(txt, f) >= threshold for f in FILLER_PHRASES)
