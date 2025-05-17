import os
import requests

def text_to_speech(text, output_audio_path='output_audio.mp3', model="aura-2-thalia-en"):
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY is not set in environment.")

    url = f"https://api.deepgram.com/v1/speak?model={model}"

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "text/plain"
    }

    try:
        print(f"[TTS] Synthesizing with Deepgram model: {model}")
        response = requests.post(url, headers=headers, data=text.encode("utf-8"))
        response.raise_for_status()

        with open(output_audio_path, "wb") as f:
            f.write(response.content)

        print(f"[TTS] Saved TTS to: {output_audio_path}")
        return output_audio_path
    except requests.exceptions.RequestException as e:
        print(f"[TTS] Deepgram API call failed: {e}")
        return None
