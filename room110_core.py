# -*- coding: utf-8 -*-
"""
Room 110: Targeted On-Demand Refactoring Agent for BedRock Compiler Backend
Scope: Issue-Driven & Context-Aware Automation via GitHub Actions
"""

import os
import re
import sys
import time
import base64
import requests

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
BEDROCK_RULES_URL = "https://bedrock.abrdns.com"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

FALLBACK_RULES = """
Rule 1: Strict MIPS byte-level and alignment validation.
Rule 2: Eliminate redundant register allocations and optimize branch delays.
Rule 3: Ensure absolute type safety inside the BedRock compiler backend IR.
Rule 4: Output pure Rust syntax exclusively bounded inside a single ```rust block.
"""

# ==========================================
# SYSTEM PROMPTS
# ==========================================
TARGETED_AGENT_PROMPT = """
You are the Senior Backend Engineer for the BedRock Compiler Project. 
Your expertise is specialized in compiler optimization, MIPS target architectures, and Rust implementation.

You are given:
1. The language and compiler specifications from the official BedRock documentation.
2. An Issue context describing a bug or required refactoring.

CRITICAL DIRECTIVES:
- Focus ONLY on the described issue.
- Identify which compiler asset is affected (e.g., mips.rs, ir_emit.rs) based on the context.
- Output your reasoning and the optimized or fixed function block in a single ```rust block.
"""

def fetch_bedrock_rules() -> str:
    """Fetches BedRock language specifications from the remote documentation site."""
    print("[🔄] Fetching BedRock documentation and language specs...")
    try:
        response = requests.get(BEDROCK_RULES_URL, timeout=12)
        if response.status_code == 200 and response.text.strip():
            print("[✅] BedRock core documentation loaded successfully.")
            return response.text
        else:
            return FALLBACK_RULES
    except Exception as e:
        return FALLBACK_RULES

class GitHubNativeClient:
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{repo}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }

    def get_default_branch(self) -> str:
        res = requests.get(self.base_url, headers=self.headers)
        return res.json().get("default_branch", "main")

    def get_branch_sha(self, branch: str) -> str:
        url = f"{self.base_url}/git/ref/heads/{branch}"
        res = requests.get(url, headers=self.headers)
        return res.json()["object"]["sha"]

    def get_repository_tree(self, branch_sha: str) -> list:
        url = f"{self.base_url}/git/trees/{branch_sha}?recursive=1"
        res = requests.get(url, headers=self.headers)
        return [item['path'] for item in res.json().get('tree', []) if item['type'] == 'blob' and item['path'].endswith('.rs')]

    def get_file_content(self, path: str, branch: str) -> tuple:
        url = f"{self.base_url}/contents/{path}?ref={branch}"
        res = requests.get(url, headers=self.headers)
        if res.status_code == 404:
            return None, None
        data = res.json()
        content_decoded = base64.b64decode(data["content"]).decode("utf-8")
        return content_decoded, data["sha"]

    def create_new_branch(self, new_branch_name: str, base_sha: str):
        url = f"{self.base_url}/git/refs"
        payload = {"ref": f"refs/heads/{new_branch_name}", "sha": base_sha}
        requests.post(url, headers=self.headers, json=payload)

    def commit_file_change(self, path: str, content: str, msg: str, branch: str, sha: str):
        url = f"{self.base_url}/contents/{path}"
        content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        payload = {"message": msg, "content": content_b64, "branch": branch, "sha": sha}
        requests.put(url, headers=self.headers, json=payload)

    def create_pull_request(self, title: str, head: str, base: str, body: str) -> str:
        url = f"{self.base_url}/pulls"
        payload = {"title": title, "head": head, "base": base, "body": body}
        res = requests.post(url, headers=self.headers, json=payload)
        return res.json().get("html_url", "PR Created")

def main():
    print("[🚀] Activating Room 110 Automated Issue-Driven Agent...")
    
    gh_token = os.getenv("GITHUB_TOKEN")
    gh_repo = os.getenv("GITHUB_REPOSITORY")
    groq_key = os.getenv("GROQ_API_KEY")
    issue_body = os.getenv("ISSUE_BODY", "").strip()
    
    if not all([gh_token, gh_repo, groq_key]):
        print("[🔴] Missing required environment credentials.")
        sys.exit(1)
        
    if not issue_body:
        print("[⚠️] No Issue Body or Comment context detected. Skipping active run.")
        return

    gh = GitHubNativeClient(gh_token, gh_repo)
    specs = fetch_bedrock_rules()
    
    base_branch = gh.get_default_branch()
    base_sha = gh.get_branch_sha(base_branch)
    
    # محاولة استخراج مسار الملف تلقائياً إذا كان مكتوباً في نص المشكلة
    all_files = gh.get_repository_tree(base_sha)
    target_file = None
    for f in all_files:
        if f in issue_body:
            target_file = f
            break
            
    # إذا لم يذكر مسار صريح، نحدد الافتراضي للمشكلة الحالية (mips.rs)
    if not target_file:
        target_file = "compiler/src/codegen/mips.rs"
        
    print(f"[🎯] Target Context Asset Identified: {target_file}")
    current_code, file_sha = gh.get_file_content(target_file, base_branch)
    
    if not current_code:
        print(f"[🔴] Could not load file content for: {target_file}")
        sys.exit(1)

    print(f"[🤖] Consulting Groq API using {GROQ_MODEL}...")
    
    user_prompt = f"""
    BedRock Specifications:
    {specs[:3000]}
    
    Reported Issue Details:
    {issue_body}
    
    Target Implementation File Context ({target_file}):
    ```rust
    {current_code[:15000]}
    ```
    Analyze and patch the bug described in the issue. Ensure proper MIPS data-symbol alignment and resolve variables correctly.
    """

    headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": TARGETED_AGENT_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
    if response.status_code != 200:
        print(f"[🔴] API Error: {response.text}")
        sys.exit(1)
        
    result = response.json()['choices'][0]['message']['content']
    print("\n=== 🧠 ANALYSIS OUTPUT ===")
    print(result)
    
    code_match = re.search(r"```rust\s*\n(.*?)\n```", result, re.DOTALL | re.IGNORECASE)
    if code_match:
        optimized_code = code_match.group(1).strip()
        
        if current_code.strip() != optimized_code:
            print("[🔥] Generating atomic feature branch and Pull Request for the solution...")
            timestamp = int(time.time())
            feature_branch = f"refactor/room110-issue-{timestamp}"
            gh.create_new_branch(feature_branch, base_sha)
            
            gh.commit_file_change(target_file, optimized_code, f"Room 110: Fix for issue context", feature_branch, file_sha)
            
            pr_body = f"### 🏛️ Room 110 Resolution\n\nAutomated fix proposed for the reported compiler issue.\n\n#### Summary of Analysis:\n{result}"
            pr_url = gh.create_pull_request(f"✨ Room 110: Automated Compiler Patch", feature_branch, base_branch, pr_body)
            print(f"[🚀] Pull Request successfully deployed: {pr_url}")
    else:
        print("[✅] No explicit code edits recommended by the model.")

if __name__ == "__main__":
    main()
