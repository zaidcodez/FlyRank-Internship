import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.getenv("LLM_API_KEY"),
    timeout=30.0,
    max_retries=0,
)

response = client.chat.completions.create(
    model=os.getenv("LLM_MODEL", "qwen/qwen3.8-27b:free"),
    messages=[
        {"role": "user", "content": "Reply with exactly: ready"}
    ],
    temperature=0,
)

print(response.choices[0].message.content.strip())