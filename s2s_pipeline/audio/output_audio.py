
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio
import threading
import pyaudio
import webrtcvad
import time
import collections

def monitor_for_voice_interrupt(rate=16000, duration_ms=30, aggressiveness=3, frame_window=10, trigger_count=3, device_index=None):
    """
    Monitors microphone input and returns True if voice is detected consistently.
    """
    if duration_ms not in [10, 20, 30]:
        raise ValueError("duration_ms must be 10, 20, or 30")

    vad = webrtcvad.Vad(aggressiveness)
    audio = pyaudio.PyAudio()

    frame_size = int(rate * duration_ms / 1000)
    byte_size = frame_size * 2

    try:
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=frame_size
        )

        print(f"[Interrupt Monitor] Listening for voice interrupt (trigger {trigger_count}/{frame_window})...")
        frame_history = collections.deque(maxlen=frame_window)

        while True:
            frame = stream.read(frame_size, exception_on_overflow=False)
            if len(frame) != byte_size:
                continue

            is_voiced = vad.is_speech(frame, rate)
            frame_history.append(is_voiced)

            bar = ''.join(['█' if v else ' ' for v in frame_history])
            print(f"\r[VAD] {bar}", end="")

            if sum(frame_history) >= trigger_count:
                print("\n[Interrupt Monitor] VOICE INTERRUPT TRIGGERED.")
                return True

            time.sleep(0.02)
    except Exception as e:
        print(f"[Interrupt Monitor] Error: {e}")
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        audio.terminate()

    return False

def play_audio_interruptible_by_voice(audio_file, device_index=None):
    from threading import Event
    interrupt_event = Event()

    audio = AudioSegment.from_file(audio_file)
    playback = None

    def monitor():
        if monitor_for_voice_interrupt(aggressiveness=3, frame_window=10, trigger_count=3, device_index=device_index):
            interrupt_event.set()
            if playback and playback.is_playing():
                playback.stop()
                print("[Playback] Stopped due to voice interrupt.")

    monitor_thread = threading.Thread(target=monitor)
    monitor_thread.daemon = True
    monitor_thread.start()

    time.sleep(0.05)  # ensure mic is warmed up

    playback = _play_with_simpleaudio(audio)
    playback.wait_done()

    return interrupt_event.is_set()
