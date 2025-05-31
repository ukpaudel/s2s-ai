"""
pipeline_core.py
───────────────────────────────────────────────────────────────────
1. Audio  ➜  VAD  ➜  Whisper ASR (local)/Deepgram ASR
2. LLM prompt (with short context)
3. LLM JSON  ➜  intent / action
4. Slot-filling & execute_action
5. Decide reply  ➜  Deepgram TTS
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Tuple
import time
import logging

def run_s2s_once(
    audio_path: str | Path,
    dialogue_manager=None,
) -> Tuple[str, str | dict, str, "DialogueManager"]:

    # ── Lazy heavy imports ────────────────────────────────────────────
    from s2s_pipeline.audio.vad_speaker_id import vad_speaker_identification
    from s2s_pipeline.asr.deepgram_asr import transcribe_audio
    #from s2s_pipeline.asr.whisper_asr import transcribe_audio
    from s2s_pipeline.dialogue.dialogue_manager import DialogueManager
    from s2s_pipeline.dialogue.prompt_engineer import enhance_prompt
    from s2s_pipeline.dialogue.conversation_classifier import needs_clarification
    #from s2s_pipeline.llm.openai_llm import call_llm
    #from s2s_pipeline.llm.llama_llm import call_llm
    from s2s_pipeline.llm.mistral_llm import call_llm
    from s2s_pipeline.llm.llm2t2c_adapter import format_llm_response
    from s2s_pipeline.tts.deepgram_tts import text_to_speech
    from s2s_pipeline.actions.action_router import execute_action
    from s2s_pipeline.utils.confirm_matcher import (
        is_affirmative, is_negative, is_cancel, looks_like_filler
    )
    # ─────────────────────────────────────────────────────────────────
    start = time.perf_counter()
    # 1️⃣ Dialogue manager
    if dialogue_manager is None:
        dialogue_manager = DialogueManager()

    # 2️⃣ ASR
    asr_start = time.perf_counter()
    processed_audio = vad_speaker_identification(audio_path)
    asr_result = transcribe_audio(processed_audio)
    user_text = asr_result["transcript"]
    print(f"[ASR] Took {time.perf_counter() - asr_start:.2f} sec")

    # 3️⃣ Quick slot-filling handlers BEFORE calling the LLM
    last_action = dialogue_manager.state.get("last_action")

    # YES / NO confirmation for recipient
    if (
        last_action
        and last_action.get("type") == "send_email"
        and last_action.get("parameters", {}).get("step") == "awaiting_recipient_confirm"
    ):
        if is_affirmative(user_text):
            last_action["parameters"]["confirm"] = True
            exec_res = execute_action(last_action)
            if isinstance(exec_res, dict):                      # need body
                dialogue_manager.state["last_action"] = exec_res["action"]
                return user_text, exec_res, text_to_speech(exec_res["response"]), dialogue_manager
            speech = exec_res                                   # done
            dialogue_manager.state.pop("last_action", None)
            return user_text, exec_res, text_to_speech(speech), dialogue_manager

        if is_negative(user_text):
            speech = "Okay, please tell me the correct e-mail address."
            return user_text, speech, text_to_speech(speech), dialogue_manager

    # BODY capture
    if (
        last_action
        and last_action.get("type") == "send_email"
        and last_action.get("parameters", {}).get("step") == "awaiting_body"
    ):
        if is_cancel(user_text):
            dialogue_manager.state.pop("last_action", None)
            speech = "Okay, I’ve cancelled the e-mail."
            return user_text, speech, text_to_speech(speech), dialogue_manager

        if looks_like_filler(user_text):
            speech = "Please tell me the message you want to send."
            return user_text, speech, text_to_speech(speech), dialogue_manager

        last_action["parameters"]["body"] = user_text
        exec_res = execute_action(last_action)
        if isinstance(exec_res, dict):                           # should not loop again
            dialogue_manager.state["last_action"] = exec_res["action"]
            return user_text, exec_res, text_to_speech(exec_res["response"]), dialogue_manager
        speech = exec_res        # sent!
        dialogue_manager.state.pop("last_action", None)
        dialogue_manager.pop_last_turn()            # existing line

        # 🆕 add: record fingerprint so we never reopen same task
        fp = f"{last_action['type']}::{last_action['parameters'].get('to','')}"
        dialogue_manager.state.setdefault("completed_actions", set()).add(fp)
        return user_text, exec_res, text_to_speech(speech), dialogue_manager

    # 4️⃣ Build prompt → call LLM
    llm_start = time.perf_counter()
    if last_action and last_action.get("parameters", {}).get("step"):
        context = dialogue_manager.get_context_snippet(skip_last=True)
    else:
        context = dialogue_manager.get_context_snippet()
    
    prompt = enhance_prompt({"user_input": user_text, "context": context})
    llm_raw = call_llm(prompt)                                   # str or dict
    print(f"[LLM] Took {time.perf_counter() - llm_start:.2f} sec")

    # 5️⃣ Parse structured response
    try:
        parsed = json.loads(llm_raw) if isinstance(llm_raw, str) else llm_raw
    except json.JSONDecodeError:
        parsed = {"response": llm_raw, "intent": "unknown"}

    intent  = parsed.get("intent", "unknown")
    action  = parsed.get("action")
    # 🛡️  If this task was already completed, downgrade to general_chat
    fp = f"{intent}::{action.get('parameters',{}).get('to','')}" if action else ""
    if fp and fp in dialogue_manager.state.get("completed_actions", set()):
        parsed.pop("action", None)
        intent = "general_chat"
        parsed["intent"] = "general_chat"
        action = None
    
    music_kw = ("music", "song", "playlist", "listen", "podcast",
            "spotify", "tune", "radio")
    if any(k in user_text.lower() for k in music_kw):
        parsed.pop("action", None)
        parsed["intent"] = "general_chat"
        intent = "general_chat"
        action = None


    # ⇢ Fallback: if intent is task but action missing – bootstrap shell
    if intent in {"send_email", "create_event", "send_sms"} and not action:
        parsed["action"] = {"type": intent, "parameters": {"to": user_text.strip()}}
        action = parsed["action"]

    # Merge actions with previous turn if same type
    if isinstance(action, dict) and action.get("type"):
        if last_action and last_action.get("type") == action.get("type"):
            merged = {**last_action.get("parameters", {}), **action.get("parameters", {})}
            action["parameters"] = merged
        dialogue_manager.state["last_action"] = action
    else:
        dialogue_manager.state.pop("last_action", None)

    # 6️⃣ Save memory
    dialogue_manager.update_state(
        user_input=user_text,
        llm_response=llm_raw,
        confidence=asr_result.get("avg_logprob"),
        intent=intent,
    )

    # 7️⃣ Decide what to speak
    if (
        isinstance(action, dict)
        and action.get("type")
        and (
            action.get("parameters", {}).get("step")         # slot-filling marker
            or action["parameters"].get("body")              # full payload
            or action["parameters"].get("to")                # ← NEW: just “to”
        )
    ):
        exec_res = execute_action(action)
        if isinstance(exec_res, dict):                           # still slot-filling
            dialogue_manager.state["last_action"] = exec_res["action"]
            tts_text = exec_res["response"]
        else:                                                    # completed
            dialogue_manager.state.pop("last_action", None)
            tts_text = exec_res or parsed.get("response", "")
            dialogue_manager.state.pop("last_action", None)   # ✅ always clear
    else:                                                        # general chat
        tts_text = parsed.get("response") if isinstance(parsed, dict) else format_llm_response(llm_raw)

    if not tts_text:
        tts_text = (
            "Could you please clarify?"
            if needs_clarification(
                llm_raw,
                avg_logprob=asr_result.get("avg_logprob"),
                no_speech_prob=asr_result.get("no_speech_prob"),
            )
            else "Sorry, I didn't catch that."
        )

    # 8️⃣ TTS
    tts_start = time.perf_counter()
    tts_path = text_to_speech(tts_text)
    print(f"[TTS] Took {time.perf_counter() - tts_start:.2f} sec")
    print(f"[Pipeline] Total time: {time.perf_counter() - start:.2f} sec")


    return user_text, llm_raw, tts_path, dialogue_manager
