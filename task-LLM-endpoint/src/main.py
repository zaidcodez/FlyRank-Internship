import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .llm.schema import TriageRequest
from .llm.service import ModelCallError, ModelTimeout, classify

app = FastAPI(title="FlyRank A17 - LLM Triage API")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid request",
            "details": exc.errors(),
        },
    )


@app.get("/")
def root():
    return {"status": "ready"}


@app.post("/triage")
def triage(request: TriageRequest):
    if os.getenv("LLM_ENABLED", "true").lower() == "false":
        return {
            "category": "other",
            "urgency": "normal",
            "confidence": 0.0,
            "reason": "LLM processing is disabled.",
        }

    if os.getenv("LLM_STUB", "0") == "1":
        return {
            "category": "other",
            "urgency": "normal",
            "confidence": 0.0,
            "reason": "Stub mode is enabled.",
        }

    try:
        result = classify(request.text)
        return result.model_dump()
    except ModelTimeout:
        return JSONResponse(
            status_code=504,
            content={"error": "LLM request timed out"},
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=422,
            content={"error": str(exc)},
        )
    except ModelCallError as exc:
        return JSONResponse(
            status_code=502,
            content={"error": "LLM provider request failed", "details": str(exc)},
        )
