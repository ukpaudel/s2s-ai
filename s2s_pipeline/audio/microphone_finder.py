
import os
import json
import pyaudio

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "mic_config.json")

def list_microphones():
    p = pyaudio.PyAudio()
    print("Available input devices:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            print(f"  [{i}] {info['name']}")
    p.terminate()

def select_microphone():
    p = pyaudio.PyAudio()
    devices = []
    print("Available input devices:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            devices.append((i, info["name"]))
            print(f"[{i}] {info['name']}")
    p.terminate()

    if not devices:
        raise RuntimeError("No input devices found.")

    while True:
        try:
            choice = int(input("Select microphone index: "))
            if any(d[0] == choice for d in devices):
                save_microphone_index(choice)
                return choice
        except ValueError:
            pass
        print("Invalid selection, try again.")

def save_microphone_index(index):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"mic_index": index}, f)

def load_microphone_index():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
            return data.get("mic_index")
    return None

def get_microphone_index():
    index = load_microphone_index()
    if index is not None:
        return index
    return select_microphone()
