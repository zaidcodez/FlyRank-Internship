import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
API_KEY = os.getenv("LLM_API_KEY")
MODEL = os.getenv("LLM_MODEL", "qwen/qwen3.8-27b:free")

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    timeout=30.0,
    max_retries=0,
)