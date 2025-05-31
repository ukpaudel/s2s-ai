import os
import requests
from dotenv import load_dotenv
load_dotenv()
LLM_API_URL = os.getenv("LLM_API_URL")

def call_llm(prompt, model=None, temperature=0.7, max_tokens=30):
    try:
        response = requests.post(
            LLM_API_URL,
            headers={"Content-Type": "application/json"},
            json={
                "model": "meta-llama/Llama-2-7b-chat-hf",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"LLM call failed: {e}")
        return "[ERROR: LLM call failed]"
