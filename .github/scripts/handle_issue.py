#!/usr/bin/env python3
# handle_issue.py
# Robust GitHub Issue -> Gemini handler for Codemaker Agent
# - safer model config (larger max tokens)
# - robust extraction (search JSON for "text")
# - friendly fallback when model stops early

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


# Basic environment checks
if not GITHUB_EVENT_PATH:
    fail("GITHUB_EVENT_PATH is not set.")
if not GITHUB_REPO:
    fail("GITHUB_REPOSITORY is not set.")
if not GITHUB_TOKEN:
    fail("GITHUB_TOKEN is not set.")
if not GEMINI_KEY:
    print("Warning: GEMINI_API_KEY not set. Model calls will be skipped and fallback posted.")


# Load event payload
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

# Build prompt
prompt = (
    "You are Codemaker Agent, a concise helpful developer assistant.\n"
    "Answer the GitHub issue below. If code is helpful, include a fenced code block.\n\n"
    f"Issue title: {issue_title}\n"
    f"Issue body: {issue_body}\n"
)

model_text: Optional[str] = None
model_raw: Optional[Dict[str, Any]] = None

if GEMINI_KEY:
    MODEL = "models/gemini-2.5-flash"
    URL = f"https://generativelanguage.googleapis.com/v1/{MODEL}:generateContent"
    # Increase max tokens to reduce MAX_TOKENS early stops
    payload: Dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024}
    }

    try:
        resp = requests.post(
            f"{URL}?key={GEMINI_KEY}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
    except Exception as e:
        print("Model call failed (network):", e)
    else:
        try:
            j = resp.json()
            model_raw = j
        except Exception:
            print("Model response not JSON:", resp.text)
            j = None

        # Robust extraction: try normal path, then search for any "text" in response
        def safe_extract_text(obj: Any) -> Optional[str]:
            if obj is None:
                    cands = obj.get("candidates", [])
                    if cands and isinstance(cands, list):
                        if parts and isinstance(parts, list) and len(parts) > 0:
                            p0 = parts[0]
                            if isinstance(p0, dict) and "text" in p0:
                                return p0.get("text")
                # Generic search
                for k, v in obj.items():
                    if k == "text" and isinstance(v, str):
                        return v
                    res = safe_extract_text(v)
                    if res:
                        return res
            elif isinstance(obj, list):
                for item in obj:
                    res = safe_extract_text(item)
                    if res:
                        return res
            return None

        if model_raw is not None:
            model_text = safe_extract_text(model_raw)

# Build comment body
if model_text:
    comment_body = f"Hello — Codemaker Agent here.\n\n{model_text}"
else:
    # If model didn't produce usable text, include a helpful fallback explanation and a short raw excerpt
    raw_excerpt = ""
    try:
        if model_raw is not None:
            # include only first ~400 characters of the JSON to avoid too large comments
            raw_excerpt = json.dumps(model_raw, indent=2)[:400]
    except Exception:
        raw_excerpt = ""

    comment_body = (
        "Hello — Codemaker Agent.\n\n"
        "I could not produce a full model response. This can happen when the model reached its token limit or returned an unexpected response shape.\n\n"
        "What you can try:\n"
        "- Shorten the issue text or ask a more specific question.\n"
        "- If you want a longer answer, ask for a shorter, focused example.\n\n"
        f"Model debug excerpt:\n```\n{raw_excerpt}\n```\n"
        "If you expect this to work and it still fails, ask me to retry or share a shorter prompt."
    )

# Post comment
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
        print("Response:", post_resp.text)
    except Exception:
        pass
    sys.exit(1)

print(f"Posted comment to issue #{issue_number}.")
sys.exit(0)                        first = cands[0]
                        content = first.get("content", {})
                        parts = content.get("parts") if isinstance(content, dict) else None
            if isinstance(obj, dict):
                # Preferred: candidates -> content -> parts -> text
                if "candidates" in obj:
                    cands = obj.get("candidates", [])
                    if cands and isinstance(cands, list):
                        first = cands[0]
                        content = first.get("content", {})
                        parts = content.get("parts") if isinstance(content, dict) else None
                        if parts and isinstance(parts, list) and len(parts) > 0:
                            p0 = parts[0]
                            if isinstance(p0, dict) and "text" in p0:
                                return p0.get("text")
                # Generic search
                for k, v in obj.items():
                    if k == "text" and isinstance(v, str):
                        return v
                    res = safe_extract_text(v)
                    if res:
                        return res
            elif isinstance(obj, list):
                for item in obj:
                    res = safe_extract_text(item)
                    if res:
                        return res
            return None

        if model_raw is not None:
            model_text = safe_extract_text(model_raw)

# Build comment body
if model_text:
    comment_body = f"Hello — Codemaker Agent here.\n\n{model_text}"
else:
    # If model didn't produce usable text, include a helpful fallback explanation and a short raw excerpt
    raw_excerpt = ""
    try:
        if model_raw is not None:
            # include only first ~400 characters of the JSON to avoid too large comments
            raw_excerpt = json.dumps(model_raw, indent=2)[:400]
    except Exception:
        raw_excerpt = ""

    comment_body = (
        "Hello — Codemaker Agent.\n\n"
        "I could not produce a full model response. This can happen when the model reached its token limit or returned an unexpected response shape.\n\n"
        "What you can try:\n"
        "- Shorten the issue text or ask a more specific question.\n"
        "- If you want a longer answer, ask for a shorter, focused example.\n\n"
        f"Model debug excerpt:\n```\n{raw_excerpt}\n```\n"
        "If you expect this to work and it still fails, ask me to retry or share a shorter prompt."
    )

# Post comment
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
        print("Response:", post_resp.text)
    except Exception:
        pass
    sys.exit(1)

print(f"Posted comment to issue #{issue_number}.")
sys.exit(0)

