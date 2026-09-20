import json
from pathlib import Path

import requests

CASES = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))

matches = 0
failures = []

for number, case in enumerate(CASES, start=1):
    try:
        response = requests.post(
            "http://127.0.0.1:8000/triage",
            json={"text": case["text"]},
            timeout=40,
        )

        data = response.json()
        actual = data.get("category")
        expected = case["expected_category"]

        if response.status_code == 200 and actual == expected:
            matches += 1
            print(f"{number}. match - {actual}")
        else:
            failures.append(
                {
                    "case": number,
                    "expected": expected,
                    "actual": actual,
                    "response": data,
                }
            )
            print(f"{number}. fail - expected {expected}, got {actual}")

    except Exception as exc:
        failures.append({"case": number, "error": str(exc)})
        print(f"{number}. fail - {exc}")

score = matches / len(CASES) * 100

print()
print(f"Score: {matches}/{len(CASES)} ({score:.1f}%)")

if failures:
    print("Failures:")
    for failure in failures:
        print(failure)
