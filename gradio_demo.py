import sys
from pathlib import Path

# Add your project root directory (adjust if needed)
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))


import gradio as gr
from api.pipeline_core import run_s2s_once

def s2s_handler(audio_file):
    transcript, response, audio_out_path = run_s2s_once(audio_file)
    return transcript, response, audio_out_path

gr.Interface(
    fn=s2s_handler,
    #inputs=gr.Audio(source="microphone", type="filepath", label="🎤 Speak now"),
    inputs=gr.Audio(type="filepath", label="🎤 Upload or Record Audio"),

    outputs=[
        gr.Text(label="📝 Transcript"),
        gr.Text(label="💬 Assistant Response"),
        gr.Audio(label="🔊 AI Voice Reply")
    ],
    title="Speech-to-Speech Voice Agent",
    description="Real-time speech-to-speech demo with LLM + TTS",
    live=True
).launch()
