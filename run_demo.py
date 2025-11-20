import os
import requests

API_KEY = os.getenv("GEMINI_API_KEY")

def model_call(prompt: str) -> str:
    """
    Real Gemini API call using Google AI Studio endpoint.
    """
    if not API_KEY:
        return "ERROR: GEMINI_API_KEY not set."
url="https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
headers={
    "Content-Type": "application/json"
}

data={
   "contents": [
       {"parts": [{"text": prompt}]}
    ]
}

response=requests.post(
    f"{url}?key={API_KEY}",
    headers=headers
    json=data
)

if response.status_code != 200:
    return f"API Error: {response.txt}"
result = response.jsonn()
return result["candidates"][0]["content"]["parts"][0]["text"]

def run_demo():
    prompts = [
        "Write a python program that prints numbers from 1 to 5."'
        "Explain what this code does: for i in range(3): print(i*2)"
    ]

    for p in prompts:
        print("=== INPUT ===")
        Print(p)
        print("\n=== OUTPUT ===")
        Print(model_call(p))
        print("=" * 40)

if __name__ == "__main__":
    print("Running Codemaker Agent Demo...")
    print("(Make sure GEMINI_API_KEY is exported.)\n")
    run_demo()
