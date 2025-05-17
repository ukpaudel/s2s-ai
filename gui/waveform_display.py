
import pyaudio
import numpy as np
import threading
import time
import tkinter as tk
from tkinter import Canvas

class WaveformDisplay(tk.Frame):
    def __init__(self, parent, width=600, height=100, rate=16000, chunk=1024):
        super().__init__(parent)
        self.width = width
        self.height = height
        self.rate = rate
        self.chunk = chunk
        self.canvas = Canvas(self, width=self.width, height=self.height, bg="black")
        self.canvas.pack()
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
        threading.Thread(target=self._update_waveform, daemon=True).start()

    def stop(self):
        self.running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()

    def _update_waveform(self):
        while self.running:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.int16)
                self._draw_waveform(samples)
            except Exception as e:
                print(f"[Waveform] Error: {e}")
                break
            time.sleep(0.03)

    def _draw_waveform(self, samples):
        self.canvas.delete("all")
        mid = self.height // 2
        scale = self.height / 2 / max(np.max(samples), 1)
        step = max(1, len(samples) // self.width)
        points = []
        for x in range(0, self.width):
            idx = x * step
            if idx < len(samples):
                y = int(mid - samples[idx] * scale)
                points.append((x, y))
        for x, y in points:
            self.canvas.create_line(x, mid, x, y, fill="lime", width=1)
