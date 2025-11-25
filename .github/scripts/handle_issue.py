#!/usr/bin/env python3
# handle_issue.py — fully corrected, indentation-safe, Gemini-compatible

import os
import json
import sys
import requests
from typing import Any, Dict, Optional

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
GITHUB_EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")


def fail(msg: str):
    print("ERROR:", msg)
    sys.exit(1)


# Environment checks
if not GITHUB_EVENT_PATH:
    fail("GITHUB_EVENT_PATH is not set.")
if not GITHUB_REPO:
    fail("GITHUB_REPOSITORY is not set.")
if not GITHUB_TOKEN:
    fail("GITHUB_TOKEN is not set.")
if not GEMINI_KEY:
    print("Warning: GEMINI_API_KEY not set. Model call will fail.")


# Load event JSON
try:
    with open(GITHUB_EVENT_PATH, "r", encoding="utf-8") as f:
        event = json.load(f)
except Exception as e:
    fail(f"Failed to load event JSON: {e}")


issue = event.get("issue")
if not issue:
    print("No issue in event — exiting.")
    sys.exit(0)

sender = event.get("sender", {})
sender_login = sender.get("login", "")
sender_type = sender.get("type", "")
if sender_type == "Bot" or sender_login.endswith("[bot]"):
    print("Bot event — skipping.")
    sys.exit(0)


issue_number = issue.get("number")
issue_title = issue.get("title", "")
issue_body = issue.get("body", "")
if not issue_number:
    fail("Missing issue number in event.")

prompt = (
    "You are Codemaker Agent. Respond concisely.\n\n"
    f"Issue title: {issue_title}\n"
    f"Issue body: {issue_body}\n"
)

model_text: Optional[str] = None
model_raw: Optional[Dict[str, Any]] = None


# ----------------------------
#  GEMINI REQUEST
# ----------------------------
if GEMINI_KEY:
    MODEL = "models/gemini-2.5-flash"
    URL = f"https://generativelanguage.googleapis.com/v1/{MODEL}:generateContent"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.25, "maxOutputTokens": 1024}
    }

    try:
        resp = requests.post(
            f"{URL}?key={GEMINI_KEY}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
    except Exception as e:
        print("Gemini network error:", e)
    else:
        try:
            model_raw = resp.json()
        except Exception:
            print("Gemini returned non-JSON:", resp.text)
            model_raw = None

        # TEXT EXTRACTION
        def search_text(o: Any) -> Optional[str]:
            if isinstance(o, dict):
                if "text" in o and isinstance(o["text"], str):
                    return o["text"]
                for v in o.values():
                    found = search_text(v)
                    if found:
                        return found
            if isinstance(o, list):
                for item in o:
                    found = search_text(item)
                    if found:
                        return found
            return None

        if model_raw:
            model_text = search_text(model_raw)


# Build comment
if model_text:
    comment_body = f"Hello — Codemaker Agent here.\n\n{model_text}"
else:
    excerpt = ""
    try:
        if model_raw:
            excerpt = json.dumps(model_raw, indent=2)[:400]
    except:
        pass

    comment_body = (
        "Hello — Codemaker Agent.\n\n"
        "I could not generate a full model response.\n\n"
        f"Debug excerpt:\n```\n{excerpt}\n```"
    )

# Post comment
comments_url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{issue_number}/comments"
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

try:
    r = requests.post(comments_url, json={"body": comment_body}, headers=headers, timeout=20)
    r.raise_for_status()
except Exception as e:
    print("Failed to post:", e)
    try:
        print("Response:", r.text)
    except:
        pass
    sys.exit(1)

print(f"Posted comment to issue #{issue_number}.")
sys.exit(0)
