import os
import requests
import re
import subprocess
import sys

# 1. جلب قواعد اللغة من موقعك مباشرة
def fetch_bedrock_rules():
    try:
        response = requests.get("https://bedrock.abrdns.com", timeout=10)
        return response.text if response.status_code == 200 else "Rule: No magic. Byte-level validation."
    except:
        return "Rule: Default BedRock rules."

# 2. محرك تعدد النماذج (Multi-Agent Debate)
def council_debate(task, code, rules, groq_key):
    prompt = f"Rules: {rules}\nTask: {task}\nCode: {code}\n"
    
    # الخبير الأول
    p1 = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {groq_key}"}, json={
        "model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": f"Propose a fix for: {prompt}"}]
    }).json()['choices'][0]['message']['content']
    
    # الخبير الثاني (ينتقد)
    p2 = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {groq_key}"}, json={
        "model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": f"Critique this proposal: {p1}. Provide a refined version with code."}]
    }).json()['choices'][0]['message']['content']
    
    return p2

# 3. التنفيذ الذكي
def execute_and_pr(consensus, token):
    code_match = re.search(r"```rust\n(.*?)\n```", consensus, re.DOTALL)
    if not code_match: return False
    
    # كتابة وتعديل
    with open("src/mips.rs", "w") as f: f.write(code_match.group(1))
    
    # Git
    subprocess.run(["git", "config", "user.name", "Room 110 Agent"])
    subprocess.run(["git", "checkout", "-b", "auto-patch"])
    subprocess.run(["git", "add", "src/mips.rs"])
    subprocess.run(["git", "commit", "-m", "Room 110: Council-approved fix"])
    subprocess.run(["git", "push", "origin", "auto-patch"])
    
    # PR
    url = f"https://api.github.com/repos/{os.getenv('GITHUB_REPOSITORY')}/pulls"
    requests.post(url, headers={"Authorization": f"token {token}"}, json={
        "title": "Council Approved Fix", "head": "auto-patch", "base": "main", "body": consensus
    })
    return True

def main():
    rules = fetch_bedrock_rules()
    code = open("src/mips.rs").read()
    issue_body = os.getenv("ISSUE_BODY", "No task provided.")
    
    consensus = council_debate(issue_body, code, rules, os.getenv("GROQ_API_KEY"))
    execute_and_pr(consensus, os.getenv("GITHUB_TOKEN"))

if __name__ == "__main__":
    main()
