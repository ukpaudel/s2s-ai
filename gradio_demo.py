import sys
from pathlib import Path

# Add your project root directory
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

import gradio as gr
from api.pipeline_core import run_s2s_once  # make sure this path is correct

def s2s_handler(audio_file):
    transcript, response, audio_out_path = run_s2s_once(audio_file)
    return transcript, response, audio_out_path

gr.Interface(
    fn=s2s_handler,
    inputs=gr.Audio(type="filepath", label="🎤 Record or Upload Audio"),
    outputs=[
        gr.Text(label="📝 Transcript"),
        gr.Text(label="💬 Assistant Response"),
        gr.Audio(label="🔊 AI Voice Reply"),
    ],
    title="Speech-to-Speech Voice Agent",
    description="🎤 Speak or upload audio. This voice agent uses Whisper ASR, GPT-4 LLM, and Deepgram TTS.",
    live=False  # optional: set to True if you want real-time updates
).launch()
