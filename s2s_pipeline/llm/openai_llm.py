# OpenAI LLM placeholder
from openai import OpenAI
import os

# Create client using the API key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_llm(prompt, model="gpt-4o-mini", temperature=0.7):
    if not client.api_key:
        raise ValueError("OPENAI_API_KEY is not set in the environment.")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM call failed: {e}")
        return "[ERROR: LLM call failed]"
