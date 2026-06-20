import os
import subprocess
import json
import requests
import re
import sys

def get_tech_context():
    url = "https://bedrock.abrdns.com"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.text[:8000]
    except:
        pass
    return "Language: BedRock (.br), Core OS: Venilla OS. No Magic. Byte-Level Validation for MIPS."

def query_groq(prompt, model_name, api_key):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model_name, "messages": [{"role": "user", "content": prompt}]}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error querying Groq: {e}")
        return None

def council_review(proposal, groq_key):
    print("[🛡️] Security Guard reviewing...")
    sec_review = query_groq(f"Critique this code for MIPS bare-metal safety and 'magic' violations: {proposal}", "llama-3.3-70b-versatile", groq_key)
    print("[🧹] QA Expert reviewing...")
    qa_review = query_groq(f"Critique this code for modularity and clean code: {proposal}", "llama-3.1-8b-instant", groq_key)
    print("[🧬] Synthesizing consensus...")
    final_report = query_groq(f"Consolidate these reviews into a final report. If the code is good, include a markdown block with the final fixed code.\nSecurity: {sec_review}\nQA: {qa_review}", "llama-3.3-70b-versatile", groq_key)
    return final_report

def apply_patch_and_open_pr(patch_content, branch_name, token):
    code_match = re.search(r"```rust\n(.*?)\n```", patch_content, re.DOTALL)
    if not code_match:
        print("[🔴] No code block found in proposal.")
        return

    # كتابة التعديل
    with open("src/mips.rs", "w") as f:
        f.write(code_match.group(1))
    
    # Git operations
    subprocess.run(["git", "config", "--global", "user.name", "Room 110 Agent"])
    subprocess.run(["git", "config", "--global", "user.email", "room110@agent.com"])
    subprocess.run(["git", "checkout", "-b", branch_name])
    subprocess.run(["git", "add", "src/mips.rs"])
    subprocess.run(["git", "commit", "-m", "Room 110: Auto-patch applied via Council consensus"])
    subprocess.run(["git", "push", "origin", branch_name])
    
    # فتح الـ PR باستخدام GitHub CLI
    os.environ["GH_TOKEN"] = token
    subprocess.run(["gh", "pr", "create", "--title", f"Auto-patch: {branch_name}", "--body", "تعديل مقترح من غرفة 110. خضع للمراجعة من قبل مجلس الخبراء. يرجى المراجعة والدمج."])
    print(f"[✅] PR created successfully.")

def main():
    groq_key = os.getenv("GROQ_API_KEY")
    token = os.getenv("GITHUB_TOKEN")
    if not groq_key or not token:
        print("[🔴] Missing required environment variables.")
        sys.exit(1)

    # 1. القراءة
    target = "src/mips.rs"
    code = open(target, "r").read() if os.path.exists(target) else ""
    
    # 2. التخطيط
    proposal = query_groq(f"Context: {get_tech_context()}\nCurrent: {code}\nTask: Propose a fix/improvement.", "llama-3.3-70b-versatile", groq_key)
    
    # 3. المراجعة
    consensus = council_review(proposal, groq_key)
    print(f"\n=== CONSENSUS ===\n{consensus}")
    
    # 4. التنفيذ
    if "```rust" in consensus:
        apply_patch_and_open_pr(consensus, f"fix/room110-{os.getenv('GITHUB_RUN_ID')}", token)

if __name__ == "__main__":
    main()
