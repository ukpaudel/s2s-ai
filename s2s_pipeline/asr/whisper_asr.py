import os
import torch
import whisper

# Optional: make sure ffmpeg is on PATH
os.environ["PATH"] += os.pathsep + "C:/ffmpeg/bin"

# Suppress warning if needed
import warnings
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

# Detect device
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("base", device=device)

def transcribe_audio(audio_path):
    print(f"Transcribing audio: {audio_path}")
    result = model.transcribe(audio_path)

    # Extract no_speech_prob from the first segment
    first_segment = result["segments"][0] if result["segments"] else {}
    no_speech_prob = first_segment.get("no_speech_prob", None)
    avg_logprob = first_segment.get("avg_logprob", None)



    return {
        "transcript": result["text"],
        "segments": result["segments"],
        "no_speech_prob": no_speech_prob,
        "avg_logprob": avg_logprob
    }