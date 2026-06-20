import os
import subprocess
import requests
import re
import sys

def get_tech_context():
    url = "https://bedrock.abrdns.com"
    try:
        response = requests.get(url, timeout=10)
        return response.text[:8000] if response.status_code == 200 else ""
    except:
        return "Language: BedRock, Architecture: MIPS."

def query_groq(prompt, model, key):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"[Error] Groq connection failed: {e}")
        return None

def apply_and_push(patch, branch_name):
    # استخراج الكود
    code_match = re.search(r"```rust\n(.*?)\n```", patch, re.DOTALL)
    if not code_match:
        print("[🔴] No code found in Rust block.")
        return False

    with open("src/mips.rs", "w") as f:
        f.write(code_match.group(1))

    # تنفيذ أوامر Git (تم إضافة --verbose للدي-بج)
    try:
        subprocess.run(["git", "config", "--global", "user.name", "Room 110 Agent"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "room110@agent.com"], check=True)
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        subprocess.run(["git", "add", "src/mips.rs"], check=True)
        subprocess.run(["git", "commit", "-m", "Room 110: Auto-patch applied"], check=True)
        subprocess.run(["git", "push", "origin", branch_name], check=True)
        print("[✅] Push successful.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[🔴] Git operation failed: {e}")
        return False

def main():
    groq_key = os.getenv("GROQ_API_KEY")
    token = os.getenv("GITHUB_TOKEN")
    if not groq_key or not token:
        print("[🔴] Missing ENV vars.")
        sys.exit(1)

    code = open("src/mips.rs", "r").read() if os.path.exists("src/mips.rs") else ""
    
    # 1. التخطيط
    print("[🚀] Starting Council Analysis...")
    proposal = query_groq(f"Context: {get_tech_context()}\nCurrent: {code}\nTask: Propose a fix.", "llama-3.3-70b-versatile", groq_key)
    
    # 2. المراجعة
    print("[🛡️] Security & QA Review...")
    consensus = query_groq(f"Review:\n{proposal}\nConsolidate into report + Rust code block.", "llama-3.3-70b-versatile", groq_key)
    print(f"\n=== CONSENSUS ===\n{consensus}")
    
    # 3. التنفيذ
    if "```rust" in consensus:
        branch = f"fix/room110-{os.getenv('GITHUB_RUN_ID', 'default')}"
        if apply_and_push(consensus, branch):
            # استخدام curl للـ API لتفادي مشاكل الـ GH CLI
            url = f"[https://api.github.com/repos/](https://api.github.com/repos/){os.getenv('GITHUB_REPOSITORY')}/pulls"
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            data = {"title": f"Auto-patch: {branch}", "head": branch, "base": "main", "body": "Proposed fix by Room 110 Council."}
            requests.post(url, headers=headers, json=data)
            print("[✅] PR Request Sent via API.")

if __name__ == "__main__":
    main()
