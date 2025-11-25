# Codemaker Agent

Short description:
Codemaker Agent is a GitHub Action + Python handler that uses Google Gemini (via Google AI Studio API) to automatically respond to GitHub issues with code suggestions and explanations.

Quick demo:
- Trigger: Open a new Issue on this repo.
- Result: The agent posts a comment with suggested code/answer.

Requirements:
- Python 3.10
- requests

Local run:
1. Create a test event file:
   cat > /tmp/test_issue_event.json <<'JSON'
   { "action":"opened", "issue":{ "number":999, "title":"Test", "body":"Explain list vs dict." }, "sender":{ "login":"you", "type":"User" } }
   JSON

2. Export env (do not put real secrets in public):
   export GITHUB_EVENT_PATH=/tmp/test_issue_event.json
   export GITHUB_REPOSITORY="hashinitnpsc-glitch/Codemaker-agent"
   export GITHUB_TOKEN="ghp_YOUR_TOKEN"     # for live posting
   export GEMINI_API_KEY="YOUR_GEMINI_KEY"   # only if you want the model to run

3. Run:
   python .github/scripts/handle_issue.py
   
# Codemaker Agent

Codemaker Agent is a GitHub-based assistant designed to help developers write, explain, run, and debug code directly through issues and pull requests. It automatically generates code snippets, provides explanations, simulates code execution, and assists with debugging questions, helping teams collaborate more efficiently on GitHub.

## Features

- Generates code snippets in multiple languages.
- Explains code posted in issues or PRs.
- Simulates code execution and displays output.
- Attempts basic debugging or error explanation.
- Easily extendable via GitHub Actions and Probot.

## Usage

Open a GitHub issue with your coding request:  
- “Write a Python loop that sums numbers.”  
- “Explain this JavaScript snippet.”  
- “Debug my error: IndexError...”  

Codemaker Agent will reply with code, explanations, simulated runs, or debugging help!
