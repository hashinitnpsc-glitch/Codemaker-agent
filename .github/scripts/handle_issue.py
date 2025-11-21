"""
issue_number = issue.get("number")
issue_title = issue.get("title", "")
issue_body = issue.get("body", "")


prompt = f"GitHub Issue Title:\n{issue_title}\n\nIssue Body:\n{issue_body}\n\nRespond as a helpful developer assistant: provide code, explanation, or next steps. Keep answer concise and include code fences for any code samples."


# Call Gemini (generateContent)
MODEL = "models/gemini-2.5-flash"
URL = f"https://generativelanguage.googleapis.com/v1/{MODEL}:generateContent"


payload: Dict[str, Any] = {
"contents": [{"parts": [{"text": prompt}]}],
"generationConfig": {
"temperature": 0.2,
"maxOutputTokens": 512
}
}


try:
resp = requests.post(f"{URL}?key={GEMINI_KEY}", json=payload, headers={"Content-Type": "application/json"}, timeout=30)
resp.raise_for_status()
except requests.RequestException as e:
comment_body = f"Codemaker Agent: error calling model API: {e}"
else:
try:
j = resp.json()
# Extract text safely
text = None
if isinstance(j, dict) and "candidates" in j:
cand = j["candidates"][0]
content = cand.get("content", {})
parts = content.get("parts", [])
if parts and isinstance(parts, list) and "text" in parts[0]:
text = parts[0]["text"]
else:
# If the model returned thoughts or other structure, fallback to pretty JSON
text = json.dumps(j, indent=2)
else:
text = json.dumps(j, indent=2)
except Exception as e:
text = f"Error parsing model response: {e}\nRaw: {resp.text if 'resp' in locals() else 'no resp'}"
comment_body = f"Hello — I am Codemaker Agent. Here is my suggestion:\n\n{ text }"


# Post comment to the issue
comments_url = f"https://api.github.com/repos/{GITHUB_REPO}/issues/{issue_number}/comments"
headers = {
"Authorization": f"token {GITHUB_TOKEN}",
"Accept": "application/vnd.github.v3+json"
}


post_payload = {"body": comment_body}
try:
post_resp = requests.post(comments_url, json=post_payload, headers=headers, timeout=20)
post_resp.raise_for_status()
print(f"Posted comment to issue #{issue_number}")
except requests.RequestException as e:
print("Failed to post comment:", e)
print("Response:", getattr(post_resp, 'text', 'no response'))
sys.exit(1)
