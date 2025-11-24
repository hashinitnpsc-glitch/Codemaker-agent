#!/usr/bin/env python3
# handle_issue.py
# GitHub Issue -> Gemini handler for Codemaker Agent
# Robust version (no open triple-quotes), safe extraction and posting.

import os
import json
import sys
import requests
from typing import Any, Dict

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
GITHUB_EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")


def fail(msg: str):
    print("ERROR:", msg)
    sys.exit(1)


if not GITHUB_EVENT_PATH:
    fail("GITHUB_EVENT_PATH is not set.")

if not GITHUB_REPO:
    fail("GITHUB_REPOSITORY is not set.")

if not GITHUB_TOKEN:
    fail("GITHUB_TOKEN is not set. The workflow must provide it.")

if not GEMINI_KEY:
    print("Warning: GEMINI_API_KEY not set. Model response will fail.")


try:
    with open(GITHUB_EVENT_PATH, "r", encoding="utf-8") as f:
        event = json.load(f)
except Exception as e:
    fail(f"Failed to load event JSON: {e}")

issue = event.get("issue")
if not issue:
    print("No 'issue' object in event — nothing to do.")
    sys.exit(0)

sender = event.get("sender", {})
sender_login = sender.get("login", "")
sender_type = sender.get("type", "")
if sender_type == "Bot" or sender_login.endswith("[bot]"):
    print("Event created by a bot — skipping to avoid loops.")
    sys.exit(0)

issue_number = issue.get("number")
issue_title = issue.get("title", "")
issue_body = issue.get("body", "")

if not issue_number:
    fail("Issue number missing in payload.")


prompt = (
    "You are Codemaker Agent.\n"
    "Respond to the GitHub issue below.\n\n"
    f"Issue title: {issue_title}\n"
    f"Issue body: {issue_body}\n"
)

model_text = None

if GEMINI_KEY:
    MODEL = "models/gemini-2.5-flash"
    URL = f"https://generativelanguage.googleapis.com/v1/{MODEL}:generateContent"
    payload: Dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 512}
    }

    try:
        resp = requests.post(
            f"{URL}?key={GEMINI_KEY}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
    except Exception as e:
        print("Model call failed:", e)
        model_text = None
    else:
        if resp.status_code != 200:
            print("Model API returned non-200 status:", resp.status_code)
            try:
                print(resp.json())
            except Exception:
                print(resp.text)
            model_text = None
        else:
            try:
                j = resp.json()
            except Exception:
                print("Model response not JSON:", resp.text)
                model_text = None
            else:
               model_text = None
try:
    # Normal expected path
    parts = j["candidates"][0]["content"].get("parts", [])
    if parts and "text" in parts[0]:
        model_text = parts[0]["text"]
    else:
        # Fallback: search anywhere for text
        def extract_text(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == "text" and isinstance(v, str):
                        return v
                    res = extract_text(v)
                    if res:
                        return res
            elif isinstance(obj, list):
                for item in obj:
                    res = extract_text(item)
                    if res:
                        return res
            return None

        extracted = extract_text(j)
        if extracted:
            model_text = extracted

except Exception:
    model_text = None

# If STILL nothing, use fallback
if not model_text:
    model_text = (
        "The model returned an incomplete response (MAX_TOKENS).\n"
        "Try shortening the issue or ask again.\n\n"
        "Raw data:\n" + json.dumps(j, indent=2)
    )
if model_text:
    comment_body = f"Hello — I am Codemaker Agent. Here is my suggestion:\n\n{model_text}"
else:
    comment_body = (
        "Hello — I am Codemaker Agent. I could not produce a model response at this time.\n\n"
        "Possible reasons: missing/invalid GEMINI_API_KEY, model API error, or temporary network issue.\n\n"
        "You can try again, or paste a short prompt here (e.g., 'Generate a Python function to reverse a string')."
    )

comments_url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{issue_number}/comments"
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

try:
    post_resp = requests.post(comments_url, json={"body": comment_body}, headers=headers, timeout=20)
    post_resp.raise_for_status()
except Exception as e:
    print("Failed to post comment:", e)
    try:
        print("Response text:", post_resp.text)
    except Exception:
        pass
    sys.exit(1)

print(f"Posted comment to issue #{issue_number}.")
sys.exit(0)
