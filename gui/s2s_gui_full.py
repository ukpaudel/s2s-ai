
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import time
import os
import datetime
import pyaudio

from s2s_pipeline.audio.audio_input import record_audio
from s2s_pipeline.audio.vad_speaker_id import vad_speaker_identification
from s2s_pipeline.asr.whisper_asr import transcribe_audio
from s2s_pipeline.dialogue.prompt_engineer import enhance_prompt
from s2s_pipeline.dialogue.conversation_classifier import needs_clarification
from s2s_pipeline.dialogue.dialogue_manager import DialogueManager
from s2s_pipeline.llm.openai_llm import call_llm
from s2s_pipeline.llm.llm2t2c_adapter import format_llm_response
from s2s_pipeline.tts.deepgram_tts import text_to_speech
from s2s_pipeline.audio.output_audio import play_audio_interruptible_by_voice
from s2s_pipeline.audio.microphone_finder import list_microphones

TRANSCRIPT_DIR = "transcripts"
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

def get_microphone_list():
    p = pyaudio.PyAudio()
    mics = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            mics.append((i, info["name"]))
    p.terminate()
    return mics

class S2SGUI:
    def __init__(self, root):
        self.root = root
        root.title("S2S Voice Agent")

        self.dialogue_manager = DialogueManager()
        self.running = False
        self.selected_mic_index = 3
        self.selected_voice = tk.StringVar(value="aura-asteria-en")
        self.transcript_log_path = os.path.join(TRANSCRIPT_DIR, f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

        self.build_ui()

    def build_ui(self):
        self.status_label = tk.Label(self.root, text="Status: Idle", font=("Arial", 14))
        self.status_label.pack(pady=5)

        mic_frame = tk.Frame(self.root)
        mic_frame.pack()
        tk.Label(mic_frame, text="🎤 Microphone:").pack(side=tk.LEFT)
        self.mic_selector = ttk.Combobox(mic_frame, state="readonly")
        mic_list = get_microphone_list()
        self.mic_selector['values'] = [f"[{i}] {name}" for i, name in mic_list]
        if mic_list:
            self.selected_mic_index = mic_list[0][0]

        self.mic_selector.bind("<<ComboboxSelected>>", self.set_selected_mic)
        self.mic_selector.pack(side=tk.LEFT, padx=5)

        voice_frame = tk.Frame(self.root)
        voice_frame.pack(pady=2)
        tk.Label(voice_frame, text="🗣 Voice Model:").pack(side=tk.LEFT)
        self.voice_selector = ttk.Combobox(voice_frame, textvariable=self.selected_voice, state="readonly")
        self.voice_selector["values"] = ["aura-asteria-en", "aura-thalia-en", "aura-orpheus-en"]
        self.voice_selector.pack(side=tk.LEFT)

        self.text_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=80, height=20, font=("Consolas", 10))
        self.text_display.pack(padx=10, pady=10)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)
        self.run_button = tk.Button(button_frame, text="▶ Start Conversation", command=self.start_pipeline, bg="green", fg="white")
        self.run_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = tk.Button(button_frame, text="■ Stop", command=self.stop_pipeline, bg="red", fg="white")
        self.stop_button.pack(side=tk.LEFT, padx=5)

    def set_selected_mic(self, event):
        selected = self.mic_selector.get()
        self.selected_mic_index = int(selected.split("]")[0][1:])

    def update_ui(self, status, message):
        self.status_label.config(text=f"Status: {status}")
        self.text_display.insert(tk.END, message + "\n")
        self.text_display.see(tk.END)
        with open(self.transcript_log_path, "a", encoding="utf-8") as f:
            f.write(f"[{status}] {message}\n")

    def pipeline_loop(self):
        self.running = True
        self.text_display.delete("1.0", tk.END)

        self.update_ui("Assistant", "Hey! How can I help you?")
        tts_text = "Hey! How can I help you?"
        audio_out = text_to_speech(tts_text, model=self.selected_voice.get())
        play_audio_interruptible_by_voice(audio_out)

        self.update_ui("Listening", "Waiting for your initial request...")
        audio_path = record_audio(device_index=self.selected_mic_index)
        processed_audio = vad_speaker_identification(audio_path)
        asr_result = transcribe_audio(processed_audio)
        transcript = asr_result['transcript']
        self.dialogue_manager.topic_seed = transcript
        self.update_ui("Topic", f"(Topic locked: {transcript})")

        while self.running:
            self.update_ui("Listening", "Recording audio...")
            audio_path = record_audio(device_index=self.selected_mic_index)

            self.update_ui("Processing", "Running VAD and Speaker ID...")
            processed_audio = vad_speaker_identification(audio_path)

            self.update_ui("Transcribing", "Transcribing audio...")
            asr_result = transcribe_audio(processed_audio)
            transcript = asr_result['transcript']
            self.update_ui("Transcript", f"User: {transcript}")

            context = self.dialogue_manager.get_context_snippet()
            base_prompt = f"Conversation so far:\n{context}\nUser: {transcript}\nAssistant:"
            llm_prompt = enhance_prompt(base_prompt, style="friendly", topic=getattr(self.dialogue_manager, "topic_seed", None))
            print('llm prompt after enhance', llm_prompt)
            self.update_ui("Thinking", "Calling LLM...")
            llm_response = call_llm(llm_prompt)
            self.update_ui("Response", f"Assistant: {llm_response}")

            self.dialogue_manager.update_state(transcript, llm_response)

            clarify = needs_clarification(
                llm_response,
                avg_logprob=asr_result.get("avg_logprob"),
                no_speech_prob=asr_result.get("no_speech_prob")
            )

            if clarify:
                tts_text = "Could you please clarify?"
            else:
                tts_text = format_llm_response(llm_response)

            self.update_ui("Speaking", f"TTS: {tts_text}")
            audio_out = text_to_speech(tts_text, model=self.selected_voice.get())
            interrupted = play_audio_interruptible_by_voice(audio_out, device_index=self.selected_mic_index)

            if interrupted:
                self.update_ui("Interrupted", "User interrupted. Listening again...")
                continue

        self.update_ui("Idle", "Stopped listening.")

    def start_pipeline(self):
        if not self.running:
            threading.Thread(target=self.pipeline_loop).start()

    def stop_pipeline(self):
        self.running = False
        self.status_label.config(text="Status: Stopped")
        self.text_display.insert(tk.END, "--- Stopped by user ---\n")
        self.text_display.see(tk.END)

def on_close():
    root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    gui = S2SGUI(root)
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
