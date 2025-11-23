#!/usr/bin/env python3
# handle_issue.py
# Simple GitHub Issue -> Gemini handler for Codemaker Agent
# Safe, robust, and avoids triple-quoted strings that can be left open.

import os
import json
import sys
import requests
from typing import Any, Dict

# Environment variables expected in Actions:
# GEMINI_API_KEY, GITHUB_TOKEN, GITHUB_REPOSITORY, GITHUB_EVENT_PATH

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
GITHUB_EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")

def fail(msg: str):
    # Print to logs and exit non-zero so Actions shows failure
    print("ERROR:", msg)
    sys.exit(1)

# Basic env checks
if not GITHUB_EVENT_PATH:
    fail("GITHUB_EVENT_PATH is not set.")

if not GITHUB_REPO:
    fail("GITHUB_REPOSITORY is not set.")

if not GITHUB_TOKEN:
    # GITHUB_TOKEN is normally provided automatically by Actions.
    fail("GITHUB_TOKEN is not set. The workflow must provide it.")

# GEMINI_KEY is optional if you only want to test posting a comment without calling model.
if not GEMINI_KEY:
    print("Warning: GEMINI_API_KEY not set. The script will still attempt to run but model calls will fail.")

# Load the GitHub event JSON (issue payload)
try:
    with open(GITHUB_EVENT_PATH, "r", encoding="utf-8") as f:
        event = json.load(f)
except Exception as e:
    fail(f"Failed to load event JSON from {GITHUB_EVENT_PATH}: {e}")

# Ensure we have an issue event
issue = event.get("issue")
if not issue:
    print("No 'issue' in event payload — exiting without action.")
    sys.exit(0)

# Skip bot events to avoid loops
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
    fail("Issue number not found in event payload.")

# Build prompt for the model
prompt_parts = [
    "You are Codemaker Agent — a helpful developer assistant.",
    "Respond to the GitHub issue below with a concise helpful reply.",
    "Include runnable code in a fenced code block if relevant.",
    "",
    "Issue title:",
    issue_title or "<no title>",
    "",
    "Issue body:",
    issue_body or "<no body>"
]
prompt = "\n".join(prompt_parts)

# If we have a Gemini key, call the model
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
        # network error
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
                # Extract model text safely
                try:
                    model_text = j["candidates"][0]["content"]["parts"][0].get("text")
                except Exception:
                    # Fallback: stringify JSON for debug
                    model_text = "Model returned unexpected shape. Raw:\n" + json.dumps(j, indent=2)

# Build comment body
if model_text:
    comment_body = f"Hello — I am Codemaker Agent. Here is my suggestion:\n\n{model_text}"
else:
    # If model didn't run, post a helpful fallback
    fallback = (
        "Hello — I am Codemaker Agent. I could not produce a model response at this time.\n\n"
        "Possible reasons: missing/invalid GEMINI_API_KEY, model API error, or temporary network issue.\n\n"
        "You can try again, or paste a short prompt here (e.g., 'Generate a Python function to reverse a string')."
    )
    comment_body = fallback

# Post comment to the issue using GITHUB_TOKEN
comments_url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{issue_number}/comments"
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
post_payload = {"body": comment_body}

try:
    post_resp = requests.post(comments_url, json=post_payload, headers=headers, timeout=20)
    post_resp.raise_for_status()
except Exception as e:
    # If posting fails, print info and exit non-zero so Actions shows failure
    print("Failed to post comment:", e)
    try:
        print("Response text:", post_resp.text)
    except Exception:
        pass
    sys.exit(1)

print(f"Posted comment to issue #{issue_number}.")
sys.exit(0)
