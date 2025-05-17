def run_s2s_once(audio_path, device_index=None):
    from s2s_pipeline.audio.vad_speaker_id import vad_speaker_identification
    from s2s_pipeline.asr.whisper_asr import transcribe_audio
    from s2s_pipeline.dialogue.dialogue_manager import DialogueManager
    from s2s_pipeline.dialogue.prompt_engineer import enhance_prompt
    from s2s_pipeline.dialogue.conversation_classifier import needs_clarification
    from s2s_pipeline.llm.openai_llm import call_llm
    from s2s_pipeline.llm.llm2t2c_adapter import format_llm_response
    from s2s_pipeline.tts.deepgram_tts import text_to_speech
    from s2s_pipeline.utils.env_check import running_on_huggingface

    dialogue_manager = DialogueManager()

    processed_audio = vad_speaker_identification(audio_path)
    asr_result = transcribe_audio(processed_audio)

    context = dialogue_manager.get_context_snippet()
    llm_input = {
        "user_input": asr_result["transcript"],
        "context": context
    }

    llm_prompt = enhance_prompt(llm_input)
    llm_response = call_llm(llm_prompt)

    dialogue_manager.update_state(
        user_input=asr_result['transcript'],
        llm_response=llm_response,
        confidence=asr_result.get('avg_logprob')
    )

    if needs_clarification(
        llm_response,
        avg_logprob=asr_result.get("avg_logprob"),
        no_speech_prob=asr_result.get("no_speech_prob")
    ):
        tts_text = "Could you please clarify?"
    else:
        tts_text = format_llm_response(llm_response)

    output_audio_path = text_to_speech(tts_text)
    return asr_result['transcript'], llm_response, output_audio_path
