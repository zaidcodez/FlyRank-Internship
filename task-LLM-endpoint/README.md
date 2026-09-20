# FlyRank A17 - LLM Triage API

This project adds one LLM-backed endpoint to a small FastAPI application.

The endpoint is for **support-message triage**. It takes one support message and returns a small validated JSON object.

## 1. Setup

Python 3.10+ is recommended.

Create a virtual environment:

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

Install packages:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env`.

This version uses **OpenRouter** with the **NVIDIA Nemotron 3 Ultra 550B A55B Free** model through OpenRouter's OpenAI-compatible API:

```text
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-v1-YOUR_KEY_HERE
LLM_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
LLM_STUB=0
LLM_ENABLED=true
```

Create an OpenRouter API key and place it in `LLM_API_KEY`.

**Do not commit `.env` or expose your API key in GitHub.**

No local model installation or Ollama setup is required.

## 2. Hello check

Run:

```bash
python src/llm/hello.py
```

It should print:

```text
ready
```

## 3. Start the API

```bash
uvicorn src.main:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

## 4. Endpoint

### POST /triage

Request:

```json
{
  "text": "I was charged twice for my subscription."
}
```

Response:

```json
{
  "category": "billing",
  "urgency": "normal",
  "confidence": 0.98,
  "reason": "The user reports a duplicate subscription charge."
}
```

Allowed categories:

* billing
* bug
* feature
* other

Allowed urgency values:

* low
* normal
* high

The request is validated before the model is called. Text longer than 2000 characters is rejected with HTTP 400.

## 5. Curl tests

Valid request:

```bash
curl -X POST http://127.0.0.1:8000/triage -H "Content-Type: application/json" -d "{\"text\":\"I was charged twice for my subscription.\"}"
```

Invalid request:

```bash
curl -X POST http://127.0.0.1:8000/triage -H "Content-Type: application/json" -d "{\"text\":\"\"}"
```

The invalid request should return HTTP 400.

## 6. Stub mode

Set:

```text
LLM_STUB=1
```

Restart the API.

The endpoint will return a deterministic response without making an LLM call.

Set it back to:

```text
LLM_STUB=0
```

when finished testing.

## 7. Kill switch

Set:

```text
LLM_ENABLED=false
```

The endpoint will stop using the model and return a deterministic fallback.

Set:

```text
LLM_ENABLED=true
```

to enable the model again.

## 8. Prompt

The prompt is kept in:

```text
prompts/triage-v1.md
```

The prompt version is logged as `triage-v1`.

The support message is sent as a separate user message instead of being inserted into the system prompt.

The model is instructed to return only the required JSON result.

## 9. Output validation and repair

The model response is treated as untrusted data.

The API:

1. Tries to extract JSON.
2. Validates it with Pydantic.
3. If parsing or validation fails, sends one repair request containing the original support message, the broken model output, the exact validation error, and a correction instruction.
4. Validates the repaired response again.
5. If it still fails, returns HTTP 422 and writes the failed response to the quarantine log.

Raw model text is not returned as the API result.

## 10. Reliability

The OpenAI-compatible client has a 30 second timeout and SDK automatic retries are disabled.

The application retries only:

* timeouts
* 429 responses
* 5xx responses

The retry delay uses exponential backoff with jitter. `Retry-After` is used when the provider supplies it.

400, 401 and 403 responses are not retried.

LLM calls also log:

* prompt version
* model
* input tokens
* output tokens
* duration
* whether repair was needed

Logs are written as JSONL under `logs/`.

The application uses **OpenRouter's OpenAI-compatible API** to access:

```text
nvidia/nemotron-3-ultra-550b-a55b:free
```

The configured model is a free model endpoint, so the listed provider token cost is `$0.00`. Token counts are still logged so the workload can be measured.

Free hosted model endpoints may have rate limits or temporary availability limitations. The application's timeout, retry, and error-handling logic is therefore retained.

## 11. Evaluation

Run the API first, then:

```bash
python evals/run_eval.py
```

The evaluation contains eight hand-labelled cases, including an ambiguous case and an instruction-injection style case.

Actual evaluation result:

```text
Score: 8/8 (100.0%)
```

Evaluation date: `2026-09-20`

Prompt version: `triage-v1`

## 12. Cost / 10k request estimate

The configured model is:

```text
nvidia/nemotron-3-ultra-550b-a55b:free
```

The model is accessed through OpenRouter.

The configured `:free` model endpoint has a listed token price of `$0.00`, so the direct provider cost for the model is currently:

```text
$0.00
```

The application records input and output token counts in:

```text
logs/llm.jsonl
```

For a 10,000-request workload, total token usage can be estimated from the average logged input and output tokens:

```text
estimated input tokens = average input tokens × 10000

estimated output tokens = average output tokens × 10000
```

Because the configured model has a listed `$0.00` token price, the direct model-token estimate for 10,000 requests is currently:

```text
$0.00
```

Free hosted endpoints can still be subject to rate limits and availability constraints. Actual workload capacity should therefore be measured using the application's token and latency logs.

## 13. What I would fix with another day

* Add more real support examples to the evaluation set.
* Improve the urgency rules using actual support-team examples.
* Add tests for more malformed model outputs.
* Add better metrics around latency and retry frequency.
* Compare the configured model against another hosted model before choosing one for production.

## 14. Project structure

```text
task-LLM-endpoint/

├── src/
│   ├── __init__.py
│   ├── main.py
│   └── llm/
│       ├── __init__.py
│       ├── client.py
│       ├── hello.py
│       ├── schema.py
│       └── service.py
├── prompts/
│   └── triage-v1.md
├── evals/
│   ├── cases.json
│   └── run_eval.py
├── logs/
│   └── .gitkeep
├── JOB-CARD.md
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

The real `.env` file and generated JSONL logs are ignored by Git.

## 15. Commits

The assignment stages are committed separately:

```text
Stage 0: define LLM job and environment
Stage 1: add triage API and schemas
Stage 2: add versioned triage prompt
Stage 3: validate and repair model output
Stage 4: document production reliability controls
Stage 5: add evaluation and finalize README
```

Do not commit `.env`.

## 16. Required work completed

This implementation covers the required A17 stages only.

Optional extras, stretch tasks, and the bonus task are intentionally not included.
