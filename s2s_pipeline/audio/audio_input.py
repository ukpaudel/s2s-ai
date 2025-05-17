import collections
import pyaudio
import wave
import webrtcvad
import time

def record_audio(
    output_filename='input_audio.wav',
    aggressiveness=1,
    rate=16000,
    frame_duration_ms=30,
    device_index=None,
    silence_duration_ms=1500,
    post_silence_buffer_ms=1000,
    max_recording_ms=20000
):
    vad = webrtcvad.Vad(aggressiveness)
    audio = pyaudio.PyAudio()

    frame_size = int(rate * frame_duration_ms / 1000)
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=rate,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=frame_size
    )

    print("Recording... (speak now)")
    frames = []
    triggered = False
    silence_counter = 0
    total_duration_ms = 0

    while True:
        frame = stream.read(frame_size)
        is_speech = vad.is_speech(frame, rate)
        total_duration_ms += frame_duration_ms

        if is_speech:
            if not triggered:
                print("Voice detected, recording...")
                triggered = True
            frames.append(frame)
            silence_counter = 0
        elif triggered:
            silence_counter += frame_duration_ms
            frames.append(frame)
            if silence_counter >= silence_duration_ms:
                print("Silence detected. Ending capture...")
                break

        if total_duration_ms >= max_recording_ms:
            print("Max recording time reached. Forcing stop.")
            break

    # Add trailing buffer after silence to capture final words
    buffer_frames = int(post_silence_buffer_ms / frame_duration_ms)
    for _ in range(buffer_frames):
        frame = stream.read(frame_size)
        frames.append(frame)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(output_filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))

    print(f"Saved audio to {output_filename}")
    return output_filename
