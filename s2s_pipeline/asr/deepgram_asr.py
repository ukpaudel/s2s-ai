"""
Deepgram ASR wrapper
────────────────────────────────────────────────────────────
• Requires:  pip install deepgram-sdk
• Set env var  DEEPGRAM_API_KEY  (or put in .env)

Returns the same structure as the old Whisper wrapper:
{
    "transcript"     : str,
    "segments"       : list[dict],
    "no_speech_prob" : float | None,
    "avg_logprob"    : float | None,
}
"""

import os, asyncio, warnings
from typing import Any, Dict, List
from deepgram import Deepgram
from dotenv import load_dotenv

load_dotenv()
DG_KEY = os.getenv("DEEPGRAM_API_KEY")
if not DG_KEY:
    raise RuntimeError("Set DEEPGRAM_API_KEY before using Deepgram ASR.")

dg = Deepgram(DG_KEY)

# ─────────────────────────────────────────────────────────────
async def _dg_transcribe(path: str) -> Dict[str, Any]:
    with open(path, "rb") as f:
        source = {"buffer": f, "mimetype": "audio/wav"}

        options = {
            "model": "nova",          # or "general"
            "punctuate": True,
            "paragraphs": False,
            "smart_format": True,
        }

        resp: Dict = await dg.transcription.prerecorded(source, options)
        return resp

# Public sync wrapper – same name/signature as before
def transcribe_audio(audio_path: str) -> Dict[str, Any]:
    """
    Deepgram → text + segments; keep return keys identical to Whisper version.
    """
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    dg_json = loop.run_until_complete(_dg_transcribe(audio_path))

    # ── Extract primary fields ─────────────────────────────
    utterance = dg_json["results"]["channels"][0]["alternatives"][0]
    text      = utterance.get("transcript", "")
    words     = utterance.get("words", [])

    # Build Whisper-style segments  (start, end, text)
    segments: List[Dict[str, Any]] = []
    if words:
        seg = {"start": words[0]["start"], "end": None, "text": ""}
        for w in words:
            # split on long gaps (≥1.0 s)
            if seg["end"] and w["start"] - seg["end"] >= 1.0:
                segments.append(seg)
                seg = {"start": w["start"], "end": None, "text": ""}
            seg["text"] += w["word"] + " "
            seg["end"]   = w["end"]
        segments.append(seg)

    # Deepgram doesn’t expose “no_speech_prob” or “avg_logprob”.
    return {
        "transcript"     : text.strip(),
        "segments"       : segments,
        "no_speech_prob" : None,
        "avg_logprob"    : None,
    }
