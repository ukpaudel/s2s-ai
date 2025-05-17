import sys
from pathlib import Path


# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

### Main file to run the full pipeline

from s2s_pipeline.audio.audio_input import record_audio
from s2s_pipeline.audio.vad_speaker_id import vad_speaker_identification
from s2s_pipeline.asr.whisper_asr import transcribe_audio
from s2s_pipeline.asr.asr2llm_adapter import prepare_llm_input
from s2s_pipeline.dialogue.dialogue_manager import DialogueManager
from s2s_pipeline.dialogue.prompt_engineer import enhance_prompt
from s2s_pipeline.dialogue.conversation_classifier import needs_clarification
from s2s_pipeline.llm.openai_llm import call_llm
from s2s_pipeline.llm.llm2t2c_adapter import format_llm_response
from s2s_pipeline.tts.deepgram_tts import text_to_speech
from s2s_pipeline.audio.output_audio import play_audio_interruptible_by_voice
from s2s_pipeline.audio.microphone_finder import get_microphone_index, list_microphones

def main():
    # Select microphone ONCE before loop
    print(list_microphones())
    device_index = get_microphone_index()

    dialogue_manager = DialogueManager()

    while True:
        audio_path = record_audio(device_index=device_index)
        processed_audio = vad_speaker_identification(audio_path)
        asr_result = transcribe_audio(processed_audio)
        print(f"[ASR] Transcript: {asr_result['transcript']}")
        if asr_result.get('no_speech_prob') is not None:
            print(f"[ASR] no_speech_prob: {asr_result['no_speech_prob']:.2f}")
        if asr_result.get('avg_logprob') is not None:
            print(f"[ASR] avg_logprob: {asr_result['avg_logprob']:.2f}")



        context = dialogue_manager.get_context_snippet()
        llm_input = prepare_llm_input(asr_result, context)
        llm_prompt = enhance_prompt(llm_input)

        llm_response = call_llm(llm_prompt)

        dialogue_manager.update_state(
            user_input=asr_result['transcript'],
            llm_response=llm_response,
            confidence=asr_result.get('avg_logprob')  # or just pass None
        )


        clarify = needs_clarification(
            llm_response,
            avg_logprob=asr_result.get("avg_logprob"),
            no_speech_prob=asr_result.get("no_speech_prob")
        )


        if clarify:
            clarification_text = "Could you please clarify?"
            audio_out = text_to_speech(clarification_text)
        else:
            formatted_response = format_llm_response(llm_response)
            audio_out = text_to_speech(formatted_response)


        interrupted = play_audio_interruptible_by_voice(audio_out, device_index=device_index)

        if interrupted:
            print("[System] Voice interrupt detected. Listening again...")
            continue  # back to main loop immediately


if __name__ == "__main__":
    main()
