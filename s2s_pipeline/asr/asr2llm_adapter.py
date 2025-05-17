# ASR to LLM adapter placeholder
def prepare_llm_input(asr_output, context_snippet=""):
    transcript = asr_output['transcript']
    prompt = f"{context_snippet}\nUser said: {transcript}\nAssistant:"
    return prompt
