"""
pipeline_core.py
───────────────────────────────────────────────────────────────────
Run one speech-to-speech turn: audio → ASR → LLM (+optional action)
→ decide reply text → TTS → return artefacts.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Tuple


def run_s2s_once(
    audio_path: str | Path,
    dialogue_manager=None,
) -> Tuple[str, str | dict, str, "DialogueManager"]:

    # Lazy heavy imports -------------------------------------------------
    from s2s_pipeline.audio.vad_speaker_id import vad_speaker_identification
    from s2s_pipeline.asr.whisper_asr      import transcribe_audio
    from s2s_pipeline.dialogue.dialogue_manager import DialogueManager
    from s2s_pipeline.dialogue.prompt_engineer  import enhance_prompt
    from s2s_pipeline.dialogue.conversation_classifier import needs_clarification
    from s2s_pipeline.llm.openai_llm      import call_llm
    from s2s_pipeline.llm.llm2t2c_adapter import format_llm_response
    from s2s_pipeline.tts.deepgram_tts    import text_to_speech
    from s2s_pipeline.actions.action_router import execute_action
    from s2s_pipeline.utils.confirm_matcher import (
    is_affirmative, is_negative, is_cancel, looks_like_filler
)


    # 1️⃣  dialogue manager
    if dialogue_manager is None:
        dialogue_manager = DialogueManager()

    # 2️⃣  ASR
    processed_audio = vad_speaker_identification(audio_path)
    asr_result      = transcribe_audio(processed_audio)
    user_text       = asr_result["transcript"]

    # ────────────────────────────────────────────────────────────────
    # QUICK GUARDS (before LLM)
    # ────────────────────────────────────────────────────────────────
    last_action = dialogue_manager.state.get("last_action")


    # YES / NO confirmation for recipient address -----------------------
    if (
        last_action
        and last_action.get("type") == "send_email"
        and last_action.get("parameters", {}).get("step") == "awaiting_recipient_confirm"
    ):

        if is_affirmative(user_text):
            last_action["parameters"]["confirm"] = True
            exec_res = execute_action(last_action)
            if isinstance(exec_res, dict):
                speech = exec_res["response"]
                dialogue_manager.state["last_action"] = exec_res["action"]
            else:
                speech = exec_res
                dialogue_manager.state.pop("last_action", None)
            return user_text, exec_res, text_to_speech(speech), dialogue_manager

        if is_negative(user_text):
            speech = "Okay, please tell me the correct e-mail address."
            return user_text, speech, text_to_speech(speech), dialogue_manager

    # ― BODY capture when waiting for message text -----------------------
    if (
        last_action
        and last_action.get("type") == "send_email"
        and last_action.get("parameters", {}).get("step") == "awaiting_body"
    ):
        if is_cancel(user_text):
            dialogue_manager.state.pop("last_action", None)
            speech = "Okay, I’ve cancelled the e-mail."
            return user_text, speech, text_to_speech(speech), dialogue_manager

        # ignore filler replies such as "yes", "okay"
        if looks_like_filler(user_text):
            speech = "Please tell me the message you want to send."
            return user_text, speech, text_to_speech(speech), dialogue_manager

        # treat utterance as the e-mail body
        last_action["parameters"]["body"] = user_text
        exec_res = execute_action(last_action)

        if isinstance(exec_res, dict):                 # should ask no more than once
            speech = exec_res["response"]
            dialogue_manager.state["last_action"] = exec_res["action"]
        else:                                          # e-mail sent
            speech = exec_res
            dialogue_manager.state.pop("last_action", None)

        return user_text, exec_res, text_to_speech(speech), dialogue_manager
    # ────────────────────────────────────────────────────────────────

    # 3️⃣  Prompt → LLM
    # Omit previous turn if we just completed an action
    if last_action and last_action.get("step") in ["awaiting_body", "awaiting_recipient_confirm"]:
        context = dialogue_manager.get_context_snippet(skip_last=True)  # Implement this
    else:
        context = dialogue_manager.get_context_snippet()

    prompt     = enhance_prompt({"user_input": user_text, "context": context})
    llm_raw    = call_llm(prompt)          # str OR dict

    # 4️⃣  parse JSON if possible + merge partial action
    try:
        parsed = json.loads(llm_raw) if isinstance(llm_raw, str) else llm_raw
    except json.JSONDecodeError:
        parsed = llm_raw

    last_action = dialogue_manager.state.get("last_action")
   # This avoids re-triggering stale actions once an email is sent and the action has been cleared.
    if (
    isinstance(parsed, dict)
    and isinstance(parsed.get("action"), dict)
    and dialogue_manager.state.get("last_action") is None  # NEW
    ):
        act = parsed["action"]
        if last_action and last_action.get("type") == act.get("type"):
            merged = {**last_action.get("parameters", {}), **act.get("parameters", {})}
            act["parameters"] = merged
        dialogue_manager.state["last_action"] = act
        parsed["action"] = act
    else:
        dialogue_manager.state.pop("last_action", None)

    # 5️⃣  save turn
    dialogue_manager.update_state(
        user_input   = user_text,
        llm_response = llm_raw,
        confidence   = asr_result.get("avg_logprob"),
    )

    # 6️⃣  choose speech
    tts_text: str | None = None

    if (
        isinstance(parsed, dict)
        and isinstance(parsed.get("action"), dict)
        and parsed["action"]
        and parsed["action"].get("type")
    ):
        exec_res = execute_action(parsed["action"])
        if isinstance(exec_res, dict):             # needs more info
            tts_text = exec_res.get("response", "")
            dialogue_manager.state["last_action"] = exec_res["action"]
        else:                                      # finished
            dialogue_manager.state.pop("last_action", None)
            tts_text = exec_res or parsed.get("response", "")

    elif isinstance(parsed, dict):
        tts_text = parsed.get("response") or format_llm_response(llm_raw)
    else:
        tts_text = format_llm_response(llm_raw)

    # fallback
    if not tts_text:
        tts_text = (
            "Could you please clarify?"
            if needs_clarification(
                llm_raw,
                avg_logprob = asr_result.get("avg_logprob"),
                no_speech_prob = asr_result.get("no_speech_prob"),
            )
            else "Sorry, I didn't catch that."
        )

    # 7️⃣  TTS
    tts_path = text_to_speech(tts_text)

    # 8️⃣  done
    return user_text, llm_raw, tts_path, dialogue_manager
