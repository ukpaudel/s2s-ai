from setuptools import setup, find_packages

setup(
    name="s2s-pipeline",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "openai",
        "pyaudio",
        "pydub",
        "webrtcvad",
        "gradio",
        "whisper @ git+https://github.com/openai/whisper.git"
    ],
    entry_points={
        "console_scripts": [
            "s2s-run=s2s_pipeline.cli:main"
        ]
    },
    include_package_data=True,
    description="Multi-turn speech-to-speech AI demo with OpenAI and Deepgram",
    author="Uttam Paudel",
    python_requires=">=3.8"
)
