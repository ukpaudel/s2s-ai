# Prompt engineer placeholder
def enhance_prompt(base_prompt, style="friendly", topic=None):
    """
    Enhances base prompt for use in speech-to-speech T2C systems.
    - Style: conversational tone
    - Topic: scoped to a locked area
    - Output constraints: speech-optimized, T2C-compatible
    """
    topic_instruction = (
        f"You are assisting the user with the topic: {topic}.\n"
        if topic else
        "You are a helpful voice assistant focused on a single technical topic.\n"
    )

    output_guidance = (
        "Speak as if you are talking directly to the user.\n"
        "Avoid tables, lists, or markdown formatting.\n"
        "Avoid visual or layout-based descriptions.\n"
        "Instead, summarize and rephrase content in a way that is natural to say aloud.\n"
        "Keep answers short and focused.\n"
        "Do not mention that you are an AI or assistant.\n"
    )

    speech_agent_reminder = (
        "You are part of a speech-to-speech (S2S) voice agent system.\n"
        "The text you generate will be immediately converted into audio using a text-to-codec model.\n"
        "Ensure the response is fluid, spoken naturally, and does not use special characters or emoji.\n"
    )

    prompt = (
        f"{speech_agent_reminder}"
        f"{topic_instruction}"
        f"{output_guidance}"
        f"Respond in a {style} tone.\n\n"
        f"{base_prompt}"
    )
    return prompt
