#fallback implementations if record_audio is not supported in HF
def record_audio(*args, **kwargs):
    raise NotImplementedError("record_audio is not supported on Hugging Face Spaces.")

def play_audio_interruptible_by_voice(*args, **kwargs):
    raise NotImplementedError("Audio playback is not supported on Hugging Face Spaces.")
