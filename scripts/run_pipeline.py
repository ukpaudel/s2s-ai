#!/usr/bin/env python
"""
scripts/run_pipeline.py
CLI loop for the multi-turn voice agent.
"""

import sys
from pathlib import Path

# Make project root importable
sys.path.append(str(Path(__file__).resolve().parent.parent))

from s2s_pipeline.audio.audio_input      import record_audio
from s2s_pipeline.audio.output_audio     import play_audio_interruptible_by_voice
from s2s_pipeline.audio.microphone_finder import get_microphone_index, list_microphones
from api.pipeline_core      import run_s2s_once
from s2s_pipeline.tts.deepgram_tts       import text_to_speech


def main() -> None:
    # ── Choose microphone once ────────────────────────────────────────
    print("Available mics:\n", list_microphones())
    device_index = get_microphone_index()   # ask user the first time / reuse later
    print(f"Using mic index: {device_index}")

    # ── Dialogue manager will be passed back & forth each turn ────────
    dialogue_manager = None

    # ── 👋 Initial greeting (TTS only) ────────────────────────────────
    greeting_text  = "Hi! How can I help you today?"
    greeting_audio = text_to_speech(greeting_text)
    play_audio_interruptible_by_voice(greeting_audio, device_index=device_index)

    # ── Main loop ─────────────────────────────────────────────────────
    while True:
        # 1. Record utterance
        audio_path = record_audio(device_index=device_index)

        # 2. One S2S turn
        transcript, llm_response, audio_out_path, dialogue_manager = run_s2s_once(
            audio_path,
            dialogue_manager
        )

        # 3. Log to console
        print(f"[User]      {transcript}")
        print(f"[Assistant] {llm_response}")

        # 4. Play assistant reply (interruptible by user voice)
        interrupted = play_audio_interruptible_by_voice(
            audio_out_path,
            device_index=device_index
        )
        if interrupted:
            print("[System] User interrupted - listening again…" )


if __name__ == "__main__":
    main()
