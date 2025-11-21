import os
import requests
import json
from typing import Any, Dict

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "models/gemini-2.5-flash"   # model you have available
METHOD = "generateContent"

URL = f"https://generativelanguage.googleapis.com/v1/{MODEL}:{METHOD}"

def model_call(prompt: str) -> str:
    if not API_KEY:
        return "ERROR: GEMINI_API_KEY not set. Export it and retry."

    # Correct payload: contents + generationConfig (place parameters here)
    payload: Dict[str, Any] = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 512
        }
    }

    try:
        resp = requests.post(
            f"{URL}?key={API_KEY}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
    except requests.RequestException as e:
        return f"Network/Error making request: {e}"

    if resp.status_code != 200:
        try:
            return "API Error: " + json.dumps(resp.json(), indent=2)
        except Exception:
            return f"API Error (non-JSON): HTTP {resp.status_code} - {resp.text}"

    try:
        j = resp.json()
    except Exception:
        return "API Error: response not JSON: " + resp.text

    try:
        return j["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return "Unexpected response shape:\n" + json.dumps(j, indent=2)

def run_demo():
    prompts = [
        "Write a Python program that prints numbers from 1 to 5.",
        "Explain what this code does: for i in range(3): print(i * 2)"
    ]

    for p in prompts:
        print("=== INPUT ===")
        print(p)
        print("\n=== OUTPUT ===")
        print(model_call(p))
        print("=" * 40)

if __name__ == "__main__":
    print("Running Codemaker Agent Demo...")
    print("(Make sure GEMINI_API_KEY is exported in this shell.)\n")
    run_demo()

