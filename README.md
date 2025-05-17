
# 🎙️ Multi-turn Speech-to-Speech AI Pipeline

A complete conversational voice agent pipeline powered by:
- **OpenAI Whisper** for speech-to-text (ASR)
- **GPT-4** (via OpenAI API) for intelligent response generation
- **Deepgram TTS** for speech synthesis (T2S)

This project enables real-time, multi-turn, voice-driven interaction using a modular pipeline.

---

## 🚀 Quick Start

### 🔑 API Keys

You must create a `.env` file in the project root containing the following environment variables:

```env
OPENAI_API_KEY=your_openai_key
DEEPGRAM_API_KEY=your_deepgram_key
```

You can use the included `.env.example` as a template.

---

### 🧰 Requirements

- Python ≥ 3.8
- [ffmpeg](https://ffmpeg.org/) installed and available on your system PATH
- Working microphone

---

### 🛠️ Installing ffmpeg (for Windows)

1. Go to: [ffmpeg download page](https://ffmpeg.org/download.html)
2. Choose "Windows builds" → e.g., [Gyan.dev builds](https://www.gyan.dev/ffmpeg/builds/)
3. Download the **"Essentials build"** ZIP (e.g., `ffmpeg-release-essentials.zip`)
4. Extract it to: `C:\ffmpeg`
5. Add `C:\ffmpeg\bin` to your system `Path` environment variable
6. Test it in terminal:
   ```bash
   ffmpeg -version
   ```

⚠️ Note: By default, the path is hardcoded in `whisper_asr.py`. If needed, edit:
```python
os.environ["FFMPEG_BINARY"] = "C:/ffmpeg/bin/ffmpeg.exe"
```

---

## 🎤 Microphone Selection

The microphone used for recording is saved in `mic_config.json` like:

```json
{ "mic_index": 3 }
```

- On first run, the app will ask you to select a microphone.
- This choice will be saved and reused.
- To reselect, simply delete `mic_config.json`.

---

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/upaudel/s2s-ai.git
   cd s2s-ai
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Install in editable mode:
   ```bash
   pip install -e .
   ```

---

## 🧪 Running the Demo

### ▶ CLI Mode
After installation, you can run the full pipeline via command line:

```bash
s2s-run
```

### 🌐 Web Demo (Gradio)
Launch a browser-based microphone demo:

```bash
python gradio_demo.py
```

> This will open a local web interface at `http://localhost:7860`

---

## 📁 Project Structure

```
s2s_pipeline/           # Core pipeline modules (ASR, TTS, LLM, etc.)
scripts/run_pipeline.py # CLI entry point for audio-based conversations
gradio_demo.py          # Web interface demo using Gradio
gui/                    # Optional GUI-based interface with waveform/VAD
```

---

## 🔐 Environment Setup

You can manage API keys and configuration with `.env`. Use the `.env.example` file to get started.

---

## 🙋 FAQ

**Q:** I’m getting `ModuleNotFoundError: no module named 's2s_pipeline'`  
**A:** Make sure your working directory is the root and you’ve added it to `sys.path` or installed the package.

**Q:** Can I use my own microphone or TTS?  
**A:** Yes — the system is modular. You can swap components or plug in your own models via the adapter files.

---

## 📜 License

MIT License

---

## ✨ Credits

- OpenAI Whisper (ASR)
- OpenAI GPT-4 (LLM)
- Deepgram Aura (TTS)
