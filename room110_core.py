# -*- coding: utf-8 -*-
"""
Room 110: Targeted Context-Aware Refactoring Agent for BedRock Compiler Backend
Scope: On-Demand Issue Resolution & Local Context Auditing
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

# سنستخدم نموذج 8b لضمان استجابة سريعة وتفادي قيود الـ TPM بالكامل
GROQ_MODEL = "llama-3.1-8b-instant"

FALLBACK_RULES = """
Rule 1: Strict MIPS byte-level and alignment validation.
Rule 2: Eliminate redundant register allocations and optimize branch delays.
Rule 3: Ensure absolute type safety inside the BedRock compiler backend IR.
Rule 4: Output pure Rust syntax exclusively bounded inside a single ```rust block.
"""

# ==========================================
# SYSTEM PROMPTS (CONTEXT-AWARE)
# ==========================================
TARGETED_AGENT_PROMPT = """
You are the Senior Backend Engineer for the BedRock Compiler Project. 
Your expertise is specialized in compiler optimization, MIPS target architectures, and Rust implementation.

You are given:
1. The language and compiler specifications from the official BedRock documentation.
2. A specific code snippet or file from the compiler backend.
3. A description of a contextual issue/bug (e.g., variable value vs. memory address conflation).

CRITICAL DIRECTIVES:
- Focus ONLY on the described issue within the provided text. Do not make unrelated structural adjustments.
- Use the BedRock specifications to guide your logic and prevent architecture hallucinations.
- If changes are needed, output the complete corrected Rust code block inside exactly one ```rust block.
- If the implementation is already correct or the description is outside the file scope, explain briefly.
"""

# ==========================================
# CORE UTILITIES
# ==========================================
def fetch_bedrock_rules() -> str:
    """Fetches BedRock language specifications from the remote documentation site."""
    print("[🔄] Fetching BedRock documentation and language specs...")
    try:
        response = requests.get(BEDROCK_RULES_URL, timeout=12)
        if response.status_code == 200 and response.text.strip():
            print("[✅] BedRock core documentation loaded successfully.")
            return response.text
        else:
            print(f"[⚠️] Unexpected response status {response.status_code}. Deploying fallback specs.")
            return FALLBACK_RULES
    except Exception as e:
        print(f"[⚠️] Failed to connect to documentation server ({str(e)}). Deploying fallback specs.")
        return FALLBACK_RULES

class GitHubNativeClient:
    """Interface with GitHub API to pull specific file contexts and handle PRs on demand."""
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

# ==========================================
# MAIN INTERACTIVE CORE
# ==========================================
def main():
    print("[🚀] Activating Room 110 Targeted On-Demand Refactoring Agent...")
    
    gh_token = os.getenv("GITHUB_TOKEN")
    gh_repo = os.getenv("GITHUB_REPOSITORY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not all([gh_token, gh_repo, groq_key]):
        print("[🔴] Environment configuration error: Missing required credentials.")
        sys.exit(1)
        
    gh = GitHubNativeClient(gh_token, gh_repo)
    specs = fetch_bedrock_rules()
    
    base_branch = gh.get_default_branch()
    base_sha = gh.get_branch_sha(base_branch)
    
    # واجهة إدخال تفاعلية لتحديد نطاق الفحص
    print("\n--- 🎯 TARGETED INTERACTION ---")
    target_file = input("📁 Enter the file path to audit (e.g., compiler/src/codegen/mips.rs): ").strip()
    issue_context = input("🔍 Describe the specific issue context (e.g., Rdf IR lowering address conflation): ").strip()
    
    if not target_file or not issue_context:
        print("[🔴] Target file path and issue context cannot be empty.")
        sys.exit(1)

    print(f"\n[🔍] Fetching operational context for '{target_file}' from GitHub...")
    current_code, file_sha = gh.get_file_content(target_file, base_branch)
    
    if not current_code:
        print(f"[🔴] Could not find or access the target file path: {target_file}")
        sys.exit(1)

    print(f"[🤖] Processing analysis using {GROQ_MODEL} with BedRock specifications constraints...")
    
    user_prompt = f"""
    BedRock Documentation & Specs:
    ---
    {specs[:4000]}  # نأخذ الجزء الأساسي من التوثيق لضمان البقاء داخل حدود الـ Tokens الآمنة
    ---
    
    Target File: {target_file}
    Reported Issue Context: {issue_context}
    
    Current Code Context:
    ```rust
    {current_code[:15000]} # فحص السياق الأساسي للملف بشكل موجه دون تخطي الحدود
    ```
    Please evaluate the problem based on the reported context and the BedRock rules. 
    Provide the resolution or optimized function block.
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

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            print(f"[🔴] Groq API returned an error status code: {response.status_code}\nDetails: {response.text}")
            sys.exit(1)
            
        result = response.json()['choices'][0]['message']['content']
        print("\n=== 🧠 AGENT PROPOSAL ANALYSIS ===")
        print(result)
        print("==================================\n")
        
        # استخراج الكود المحدث إذا وجد
        code_match = re.search(r"```rust\s*\n(.*?)\n```", result, re.DOTALL | re.IGNORECASE)
        if code_match:
            optimized_code = code_match.group(1).strip()
            
            confirm = input("💾 Do you want the agent to automatically push this fix to a new branch and open a PR? (yes/no): ").strip().lower()
            if confirm == 'yes':
                timestamp = int(time.time())
                feature_branch = f"refactor/room110-targeted-{timestamp}"
                gh.create_new_branch(feature_branch, base_sha)
                
                # كتابة التعديل على الفرع الجديد
                gh.commit_file_change(
                    target_file, 
                    optimized_code, 
                    f"Room 110: Targeted fix for {issue_context}", 
                    feature_branch, 
                    file_sha
                )
                
                # فتح Pull Request موجه
                pr_body = f"### 🏛️ Room 110 Targeted Resolution\n\n**File:** `{target_file}`\n**Context Identified:** {issue_context}\n\n#### Analysis Output:\n{result}"
                pr_url = gh.create_pull_request(
                    f"✨ Room 110: Fix for {issue_context}", 
                    feature_branch, 
                    base_branch, 
                    pr_body
                )
                print(f"[🚀🎉] Targeted Pull Request deployed successfully: {pr_url}")
        else:
            print("[✅] Audit completed. No codebase intervention or code rewrite was proposed by the agent.")
            
    except Exception as e:
        print(f"[🔴] Operational exception occurred: {str(e)}")

if __name__ == "__main__":
    main()
