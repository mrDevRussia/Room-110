import os
import requests
import re
import subprocess
import sys

# 1. جلب قواعد اللغة من موقعك مباشرة
def fetch_bedrock_rules():
    try:
        response = requests.get("https://bedrock.abrdns.com", timeout=10)
        return response.text if response.status_code == 200 else "Rule: No magic. Byte-level validation for MIPS."
    except:
        return "Rule: No magic. Byte-level validation for MIPS."

# 2. حلقة النقاش (Multi-Agent Debate)
def council_debate(task, code, rules, groq_key):
    # خبير يقترح
    p1 = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {groq_key}"}, json={
        "model": "llama-3.3-70b-versatile", 
        "messages": [{"role": "system", "content": f"Rules: {rules}"}, {"role": "user", "content": f"Task: {task}\nCurrent Code:\n{code}\nPropose a fix."}]
    }).json()['choices'][0]['message']['content']
    
    # خبير ينتقد ويعدل
    p2 = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {groq_key}"}, json={
        "model": "llama-3.3-70b-versatile", 
        "messages": [{"role": "system", "content": f"Rules: {rules}"}, {"role": "user", "content": f"Critique this proposal: {p1}. Refine it and provide final Rust code in ```rust block```."}]
    }).json()['choices'][0]['message']['content']
    
    return p2

# 3. التنفيذ
def execute_and_pr(consensus, token, repo):
    code_match = re.search(r"```rust\n(.*?)\n```", consensus, re.DOTALL)
    if not code_match: return False
    
    # كتابة التعديل
    if not os.path.exists("src"): os.makedirs("src")
    with open("src/mips.rs", "w") as f: f.write(code_match.group(1))
    
    # Git
    subprocess.run(["git", "config", "user.name", "Room 110 Agent"])
    subprocess.run(["git", "config", "user.email", "room110@agent.com"])
    branch = f"patch-{os.getenv('GITHUB_RUN_ID')}"
    subprocess.run(["git", "checkout", "-b", branch])
    subprocess.run(["git", "add", "src/mips.rs"])
    subprocess.run(["git", "commit", "-m", "Room 110: Council-approved fix"])
    subprocess.run(["git", "push", "origin", branch])
    
    # PR
    url = f"https://api.github.com/repos/{repo}/pulls"
    requests.post(url, headers={"Authorization": f"token {token}"}, json={
        "title": "Council Approved Fix", "head": branch, "base": "main", "body": consensus
    })
    return True
    
def call_groq(prompt):
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": f"Rules: {rules}"}, {"role": "user", "content": prompt}]
        }
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        
        # بدل ما نعتمد على .json()، هنطبع الرد الخام لو حصل خطأ
        if response.status_code != 200:
            print(f"[🔴] API FAILED with status {response.status_code}")
            print(f"[🔴] RAW RESPONSE: {response.text}") # ده اللي هيقولنا المشكلة الحقيقية
            sys.exit(1)
            
        data = response.json()
        return data['choices'][0]['message']['content']


def main():
    rules = fetch_bedrock_rules()
    code = open("src/mips.rs").read() if os.path.exists("src/mips.rs") else ""
    task = os.getenv("ISSUE_BODY", "No specific task.")
    
    # ابدأ النقاش
    consensus = council_debate(task, code, rules, os.getenv("GROQ_API_KEY"))
    
    # نفذ الـ PR
    if execute_and_pr(consensus, os.getenv("GITHUB_TOKEN"), os.getenv("GITHUB_REPOSITORY")):
        print("PR successfully created.")

if __name__ == "__main__":
    main()
