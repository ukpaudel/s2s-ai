# LLM to T2C adapter placeholder
import re

def sanitize_for_speech(text):
    # Remove emojis and symbols, but preserve normal spacing and punctuation
    text = re.sub(r"[^\w\s.,?!']", '', text)  # Keep letters, spaces, punctuation
    text = re.sub(r"\s+", " ", text)          # Normalize spacing (but keep it!)
    return text.strip()


def format_llm_response(raw_response):
    return sanitize_for_speech(raw_response)

