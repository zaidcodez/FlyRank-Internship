import json
import os
import random
import re
import time
from pathlib import Path

from openai import APIStatusError, APITimeoutError, APIConnectionError

from .client import MODEL, client
from .schema import TriageResult

PROMPT_VERSION = "triage-v1"
PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "triage-v1.md"
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(exist_ok=True)


class ModelTimeout(Exception):
    pass


class ModelCallError(Exception):
    pass


def load_prompt():
    return PROMPT_PATH.read_text(encoding="utf-8")


def extract_json(text: str):
    text = text.strip()

    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found")
        return json.loads(text[start:end + 1])


def validate_output(raw):
    return TriageResult.model_validate(raw)


def log_event(event):
    path = LOG_DIR / "llm.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def log_quarantine(input_text, raw_output, error):
    path = LOG_DIR / "quarantine.jsonl"
    event = {
        "input": input_text,
        "model_output": raw_output,
        "error": str(error),
        "prompt_version": PROMPT_VERSION,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def get_retry_after(exc):
    try:
        value = exc.response.headers.get("retry-after")
        if value is not None:
            return float(value)
    except Exception:
        pass
    return None


def is_retryable(exc):
    if isinstance(exc, (APITimeoutError, APIConnectionError)):
        return True

    if isinstance(exc, APIStatusError):
        status = getattr(exc, "status_code", None)
        return status == 429 or (status is not None and 500 <= status <= 599)

    return False


def call_model(messages):
    last_error = None

    for attempt in range(3):
        started = time.perf_counter()

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.1,
            )

            duration_ms = round((time.perf_counter() - started) * 1000)
            usage = getattr(response, "usage", None)

            usage_data = {
                "input_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
                "output_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
            }

            return response.choices[0].message.content or "", duration_ms, usage_data

        except (APITimeoutError, APIConnectionError, APIStatusError) as exc:
            last_error = exc

            if not is_retryable(exc) or attempt == 2:
                if isinstance(exc, APITimeoutError):
                    raise ModelTimeout() from exc
                raise ModelCallError(str(exc)) from exc

            retry_after = get_retry_after(exc)
            if retry_after is not None:
                delay = retry_after
            else:
                delay = 2 ** attempt + random.uniform(0, 0.25)

            time.sleep(delay)

    raise ModelCallError(str(last_error))


def classify(text):
    system_prompt = load_prompt()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]

    raw_output, duration_ms, usage = call_model(messages)

    try:
        result = validate_output(extract_json(raw_output))
        repair = False
    except Exception as first_error:
        repair = True

        repair_messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Your previous answer was rejected.\n\n"
                    "Original support message:\n"
                    f"{text}\n\n"
                    "Your previous answer:\n"
                    f"{raw_output}\n\n"
                    "Validation error:\n"
                    f"{first_error}\n\n"
                    "Return only corrected JSON matching the required schema."
                ),
            },
        ]

        raw_output, repair_duration, repair_usage = call_model(repair_messages)
        duration_ms += repair_duration
        usage["input_tokens"] += repair_usage["input_tokens"]
        usage["output_tokens"] += repair_usage["output_tokens"]

        try:
            result = validate_output(extract_json(raw_output))
        except Exception as second_error:
            log_quarantine(text, raw_output, second_error)
            raise ValueError("Model output could not be validated") from second_error

    log_event(
        {
            "prompt_version": PROMPT_VERSION,
            "model": MODEL,
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "duration_ms": duration_ms,
            "repair": repair,
            "estimated_cost_usd": 0.0,
        }
    )

    return result
