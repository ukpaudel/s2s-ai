# Conversation classifier placeholder
def needs_clarification(llm_response, avg_logprob=None, no_speech_prob=None):
    # Case 1: Whisper thinks there's no speech
    if no_speech_prob is not None and no_speech_prob > 0.7:
        return True

    # Case 2: Whisper's log-probability is very low (less confident)
    if avg_logprob is not None and avg_logprob < -1.2:
        return True

    unclear_phrases = [
        "i'm not sure", "can you repeat", "i didn’t understand",
        "could you clarify", "i don't understand", "what do you mean", "can you rephrase"
    ]

    llm_response_lower = llm_response.lower()
    if any(phrase in llm_response_lower for phrase in unclear_phrases):
        return True

    return False
