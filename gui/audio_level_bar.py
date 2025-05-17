
import pyaudio
import numpy as np
import threading
import tkinter as tk
from tkinter import Canvas

class AudioLevelBar(tk.Frame):
    def __init__(self, parent, width=300, height=20, rate=16000, chunk=512):
        super().__init__(parent)
        self.width = width
        self.height = height
        self.canvas = Canvas(self, width=self.width, height=self.height, bg="black")
        self.canvas.pack()
        self.rate = rate
        self.chunk = chunk
        self.running = False
        self.stream = None
        self.audio = pyaudio.PyAudio()

    def start(self, device_index=None):
        self.running = True
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=self.rate,
                                      input=True,
                                      input_device_index=device_index,
                                      frames_per_buffer=self.chunk)
        threading.Thread(target=self._update_meter, daemon=True).start()

    def stop(self):
        self.running = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
        self.stream = None

    def _update_meter(self):
        while self.running:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                level = np.abs(audio_data).mean()
                self._draw_level(level)
            except Exception as e:
                print(f"[AudioLevelBar] Error: {e}")
                break

    def _draw_level(self, level):
        self.canvas.delete("all")
        max_level = 5000  # Tunable threshold
        bar_width = int(min(level / max_level, 1.0) * self.width)
        self.canvas.create_rectangle(0, 0, bar_width, self.height, fill="lime")
