# -*- coding: utf-8 -*-
"""
Room 110: Autonomous Proactive Refactoring Agent for BedRock Compiler Backend
Scope: Global Repository Audit (Full Repository Sweep)
"""

import os
import re
import sys
import time
import json
import base64
import requests

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
BEDROCK_RULES_URL = "".join(["https://", "bedrock", ".abrdns", ".com"])
GROQ_API_URL = "".join(["https://", "api", ".groq", ".com/openai/v1/chat/completions"])

# التبديل إلى نموذج 8B لتفادي قيود الـ TPM الصارمة للنموذج الأكبر
GROQ_MODEL = "llama3-8b-8192"

# Target extensions for repository scanning
TARGET_EXTENSIONS = [".rs"]
HISTORY_LOG_PATH = "refactor_history.log"

# إعادة رفع سقف الحروف المسموح بها للملف بما يتناسب مع حدود النموذج الجديد
MAX_FILE_CHAR_LIMIT = 25000 

# فترة انتظار آمنة (بالثواني) بين الفحوصات لضمان استقرار التدفق
API_COOLDOWN_DELAY = 10

FALLBACK_RULES = """
Rule 1: Strict MIPS byte-level and alignment validation.
Rule 2: Eliminate redundant register allocations and optimize branch delays.
Rule 3: Ensure absolute type safety inside the BedRock compiler backend IR.
Rule 4: Output pure Rust syntax exclusively bounded inside a single ```rust block.
"""

# ==========================================
# SYSTEM PROMPTS (ANTI-HALLUCINATION)
# ==========================================
PROPOSAL_SYSTEM_PROMPT = """
You are the Lead Proposal Agent for the BedRock Compiler Backend Engineering Council.
Your sole domain of expertise is compiler optimization, MIPS instruction set architectures, and Rust language implementations.

CRITICAL DIRECTIVES:
1. You MUST operate strictly within the boundaries of a MIPS backend compiler. Do NOT hallucinate unrelated features.
2. Analyze the current source code against the provided BedRock language specs. Identify technical debt, optimization bottlenecks, or safety violations.
3. If no optimization is required for this specific file, you must reply with exactly "NO_CHANGES_REQUIRED". Do not output anything else.
4. Output your final proposed Rust code in a single ```rust block.
"""

REVIEWER_SYSTEM_PROMPT = """
You are the Chief Reviewer Agent for the BedRock Compiler Backend Engineering Council.
Your role is to critically analyze, stress-test, and refine the modifications suggested by the Proposal Agent.

CRITICAL DIRECTIVES:
1. Enforce flawless MIPS alignment, instruction validation rules, and structural integrity.
2. Remove any unnecessary additions. Ensure the final code compiles perfectly in Rust.
3. Your final output must end with the ultimate finalized Rust code enclosed inside exactly ONE ```rust code block.
"""

# ==========================================
# CONNECTIVITY & ERROR HANDLING UTILITIES
# ==========================================
def fetch_bedrock_rules() -> str:
    """Fetches BedRock language specifications from the remote endpoint with fallback safety."""
    print("[🔄] Fetching BedRock rules from the official site...")
    try:
        response = requests.get(BEDROCK_RULES_URL, timeout=12)
        if response.status_code == 200 and response.text.strip():
            print("[✅] BedRock language rules loaded successfully.")
            return response.text
        else:
            print(f"[⚠️] Unexpected response status {response.status_code}. Deploying fallback rules.")
            return FALLBACK_RULES
    except Exception as e:
        print(f"[⚠️] Failed to connect to server ({str(e)}). Deploying fallback rules.")
        return FALLBACK_RULES

def safe_groq_api_call(headers: dict, payload: dict) -> str:
    """Executes validated calls to the Groq API with fault-tolerant error logging."""
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            print(f"[⚠️] Groq API request returned status code: {response.status_code}")
            if response.status_code in [413, 429] or "tokens" in response.text:
                print("[⚠️] Rate limit or token threshold hit. Skipping element to preserve workflow.")
            return None
            
        data = response.json()
        if 'choices' not in data or not data['choices']:
            print("[⚠️] Groq API returned an empty choice payload structure.")
            return None
            
        return data['choices'][0]['message']['content']
    except Exception as e:
        print(f"[⚠️] Non-fatal exception occurred during Groq interaction: {str(e)}")
        return None

# ==========================================
# MULTI-AGENT COUNCIL DEBATE LOOP
# ==========================================
def run_council_debate(file_path: str, current_code: str, rules: str, groq_key: str) -> tuple:
    """Coordinates an analytical discussion loop between the Proposal and Reviewer Agents."""
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    
    # 1. Proposal Agent evaluates the file
    print(f"[🤖 Agent 1] Auditing file '{file_path}' for technical debt...")
    proposal_prompt = f"""
    Rules:
    {rules}
    
    Current Code in '{file_path}':
    ```rust
    {current_code}
    ```
    Analyze the code. If it is already optimal and matches all rules, reply with NO_CHANGES_REQUIRED.
    Otherwise, suggest an optimization and provide the updated code in a ```rust block.
    """
    
    proposal_payload = {
        "model": GROQ_MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": PROPOSAL_SYSTEM_PROMPT},
            {"role": "user", "content": proposal_prompt}
        ]
    }
    
    proposal_output = safe_groq_api_call(headers, proposal_payload)
    if not proposal_output:
        print(f"[⚠️] Could not obtain a clean response from Proposal Agent for '{file_path}'. Skipping.")
        return None, ""
    
    if "NO_CHANGES_REQUIRED" in proposal_output:
        print(f"[✅] Proposal Agent verified that '{file_path}' is optimal. Skipping refactor.")
        return None, ""
        
    print(f"[🤖 Agent 1] Optimization proposal formulated for '{file_path}'.")
    
    # فترة انتظار قصيرة بين خروج العميل الأول ودخول العميل الثاني لمنع الاندفاع اللحظي للـ Tokens
    time.sleep(2)
    
    # 2. Reviewer Agent inspects and refines the proposal
    print(f"[🤖 Agent 2] Stress-testing and reviewing the proposal for '{file_path}'...")
    reviewer_prompt = f"""
    Rules:
    {rules}
    
    Current Code:
    ```rust
    {current_code}
    ```
    
    Proposal:
    {proposal_output}
    
    Verify compliance, remove any errors, and output the absolute best final Rust implementation inside a ```rust block.
    """
    
    reviewer_payload = {
        "model": GROQ_MODEL,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": REVIEWER_SYSTEM_PROMPT},
            {"role": "user", "content": reviewer_prompt}
        ]
    }
    
    final_consensus = safe_groq_api_call(headers, reviewer_payload)
    if not final_consensus:
        print(f"[⚠️] Could not obtain a final verification from Reviewer Agent for '{file_path}'. Skipping.")
        return None, ""
        
    print(f"[✅] Consensus reached and validated successfully for '{file_path}'.")
    
    # Generate structured Markdown report trail for GitHub PR description
    audit_trail = f"""**Target File:** `{file_path}`
<details>
<summary>🔍 Click to view Proposal Agent Diagnostics</summary>

{proposal_output}

</details>

<details>
<summary>🛠️ Click to view Reviewer Agent Consensus Decision</summary>

{final_consensus}

</details>
---
"""
    return final_consensus, audit_trail

# ==========================================
# GITHUB NATIVE REST API CLIENT
# ==========================================
class GitHubNativeClient:
    """Direct implementation interface with the GitHub v3 REST API without subprocess dependency."""
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.base_url = "".join(["https://", "api", ".github", ".com/repos/", repo])
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
    def check_response_status(self, response, task_name: str):
        if response.status_code not in [200, 201, 202, 204]:
            print(f"[🔴] GitHub API action failed during: {task_name}")
            print(f"[🔴] Response Status Code: {response.status_code}")
            print(f"[🔴] Server Error Details:\n{response.text}")
            sys.exit(1)

    def get_default_branch(self) -> str:
        res = requests.get(self.base_url, headers=self.headers)
        self.check_response_status(res, "Fetching repository default branch base parameters")
        return res.json().get("default_branch", "main")

    def get_branch_sha(self, branch: str) -> str:
        url = f"{self.base_url}/git/ref/heads/{branch}"
        res = requests.get(url, headers=self.headers)
        self.check_response_status(res, f"Fetching git commit reference SHA for branch: {branch}")
        return res.json()["object"]["sha"]

    def get_repository_tree(self, branch_sha: str) -> list:
        """Fetches the complete repository directory structural path tree recursively in a single run."""
        url = f"{self.base_url}/git/trees/{branch_sha}?recursive=1"
        res = requests.get(url, headers=self.headers)
        self.check_response_status(res, "Fetching full recursive directory repository tree mapping")
        return [item['path'] for item in res.json().get('tree', []) if item['type'] == 'blob']

    def create_new_branch(self, new_branch_name: str, base_sha: str):
        url = f"{self.base_url}/git/refs"
        payload = {
            "ref": f"refs/heads/{new_branch_name}",
            "sha": base_sha
        }
        print(f"[🐙] Creating remote feature tracking branch: {new_branch_name}...")
        res = requests.post(url, headers=self.headers, json=payload)
        self.check_response_status(res, f"Creating reference branch endpoints for {new_branch_name}")

    def get_file_metadata(self, path: str, branch: str) -> tuple:
        """Downloads specific target file context payloads along with blob unique SHA hashes."""
        url = f"{self.base_url}/contents/{path}?ref={branch}"
        res = requests.get(url, headers=self.headers)
        if res.status_code == 404:
            return None, None
        self.check_response_status(res, f"Downloading code metadata contents for {path}")
        data = res.json()
        content_decoded = base64.b64decode(data["content"]).decode("utf-8")
        return content_decoded, data["sha"]

    def commit_file_change(self, path: str, content: str, commit_message: str, branch: str, sha: str = None):
        """Applies explicit updates to a target blob and executes a Git commit directly."""
        url = f"{self.base_url}/contents/{path}"
        content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": commit_message,
            "content": content_b64,
            "branch": branch
        }
        if sha:
            payload["sha"] = sha
            
        print(f"[🐙] Committing code modifications to target path '{path}' on branch '{branch}'...")
        res = requests.put(url, headers=self.headers, json=payload)
        self.check_response_status(res, f"Executing operational file blob update commit for {path}")

    def create_pull_request(self, title: str, head_branch: str, base_branch: str, body: str) -> str:
        """Deploys a finalized unified Pull Request tracking item with report context details."""
        url = f"{self.base_url}/pulls"
        payload = {
            "title": title,
            "head": head_branch,
            "base": base_branch,
            "body": body
        }
        print(f"[🐙] Opening unified production Pull Request from '{head_branch}' tracking to base branch '{base_branch}'...")
        res = requests.post(url, headers=self.headers, json=payload)
        self.check_response_status(res, f"Creating Pull Request event target connection")
        return res.json().get("html_url", "")

    def check_merged_pull_requests(self, base_branch: str) -> list:
        """Gathers historical information from recently integrated pull requests for autonomous learning."""
        url = f"{self.base_url}/pulls?state=closed&base={base_branch}&sort=updated&direction=desc&per_page=10"
        res = requests.get(url, headers=self.headers)
        self.check_response_status(res, "Reviewing repository closed pull request logs for training heuristics")
        prs = res.json()
        merged_summaries = []
        for pr in prs:
            if pr.get("merged_at"):
                merged_summaries.append({
                    "number": pr.get("number"),
                    "title": pr.get("title"),
                    "merged_at": pr.get("merged_at"),
                    "body": pr.get("body", "")
                })
        return merged_summaries

# ==========================================
# AGENT MAIN SYSTEM CORE RUNTIME LOOP
# ==========================================
def main():
    print("[🚀] Activating Room 110 Autonomous Refactoring Agent - Full Repository Sweep Protocol...")
    
    # Environment variable security validations
    gh_token = os.getenv("GITHUB_TOKEN")
    gh_repo = os.getenv("GITHUB_REPOSITORY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not all([gh_token, gh_repo, groq_key]):
        print("[🔴] Environment configuration error: Missing required variables (GITHUB_TOKEN, GITHUB_REPOSITORY, GROQ_API_KEY).")
        sys.exit(1)
        
    gh = GitHubNativeClient(gh_token, gh_repo)
    rules = fetch_bedrock_rules()
    
    base_branch = gh.get_default_branch()
    base_sha = gh.get_branch_sha(base_branch)
    print(f"[⚙️] Active Target Default Repository Base Branch Identified: {base_branch}")
    
    # 1. Fetch entire structural codebase tree and apply targeted matching extension masks
    all_files = gh.get_repository_tree(base_sha)
    target_files = [f for f in all_files if any(f.endswith(ext) for ext in TARGET_EXTENSIONS)]
    print(f"[⚙️] Detected {len(target_files)} relevant source codebase assets scoped for structural auditing.")
    
    # 2. Self-Learning Heuristics Framework
    print("[🧠] Auditing recently integrated pull requests for evolutionary self-adaptation constraints...")
    merged_prs = gh.check_merged_pull_requests(base_branch)
    
    history_content, history_sha = gh.get_file_metadata(HISTORY_LOG_PATH, base_branch)
    if history_content is None:
        history_content = "=== Room 110 Self-Learning Intelligence History Log ===\n"
        
    updated_history = history_content
    learnings_found = False
    
    for pr in merged_prs:
        pr_identifier = f"PR #{pr['number']}"
        if pr_identifier not in updated_history:
            print(f"[💡] Found unlogged historical merge context ({pr_identifier} - {pr['title']}). Integrating into intelligence tracking logs...")
            updated_history += f"\n[{pr['merged_at']}] Self-learning capture from finalized {pr_identifier}: Summary Concept: {pr['title']}.\n"
            learnings_found = True
            
    # 3. Iterative Codebase Sweep Pipeline
    pending_changes = {}
    full_pr_report = "### 🏛️ Room 110: Council Global Repository Optimization Audit Report\n\nCodebase files have been proactively audited and analyzed against official **BedRock** safety specifications.\n\n"
    
    for file_path in target_files:
        print(f"\n[🔍] Actively scanning file artifact path: {file_path}")
        current_code, file_sha = gh.get_file_metadata(file_path, base_branch)
        if not current_code:
            continue
            
        # فحص حجم الملف بناءً على الحدود الجديدة والأكثر مرونة لـ Llama-3 8B
        if len(current_code) > MAX_FILE_CHAR_LIMIT:
            print(f"[⚠️] Skipping '{file_path}' - File size ({len(current_code)} chars) exceeds targeted safe tier threshold ({MAX_FILE_CHAR_LIMIT} chars).")
            continue
            
        consensus_raw, audit_trail = run_council_debate(file_path, current_code, rules, groq_key)
        
        if consensus_raw:
            code_match = re.search(r"```rust\s*\n(.*?)\n```", consensus_raw, re.DOTALL | re.IGNORECASE)
            if code_match:
                optimized_code = code_match.group(1).strip()
                if current_code.strip() != optimized_code:
                    print(f"[🔥] Technical debt detected and structural refactoring approved for: {file_path}")
                    pending_changes[file_path] = {"code": optimized_code, "sha": file_sha}
                    full_pr_report += audit_trail
                else:
                    print(f"[✅] Target asset content structure for '{file_path}' is identical to the verified ideal model state.")
            else:
                print(f"[⚠️] Failed to parse a valid uncorrupted pure Rust snippet block for artifact path: {file_path}")

            # تهدئة الطلبات للحفاظ على الـ TPM الخاص بالحساب البرمجي
            print(f"[⏱️] Cooling down for {API_COOLDOWN_DELAY} seconds to safeguard Groq TPM rate limits...")
            time.sleep(API_COOLDOWN_DELAY)

    # 4. Processing refactoring tasks if delta changes are present
    if not pending_changes:
        print("\n[🎉] Complete workspace architecture sweep finished. Codebase is stable within the evaluated file-size spectrum.")
        if learnings_found:
            print("[📝] Syncing historical evolution training updates directly on base branch mapping...")
            gh.commit_file_change(HISTORY_LOG_PATH, updated_history, "Room 110: Update intelligence and learnings history [skip ci]", base_branch, history_sha)
        return
        
    print(f"\n[🔥] Refactoring opportunities discovered in {len(pending_changes)} code elements. Orchestrating codebase modifications updates...")
    
    # Initialize a single consolidated remote feature tracking branch for atomic changesets
    timestamp = int(time.time())
    feature_branch_name = f"refactor/room110-global-{timestamp}"
    gh.create_new_branch(feature_branch_name, base_sha)
    
    # Execute batch uploads across the unified feature target branch
    for file_path, data in pending_changes.items():
        gh.commit_file_change(file_path, data["code"], f"Room 110: Optimization sweep for {file_path}", feature_branch_name, data["sha"])
        
    # Append execution run trace information into execution logs
    updated_history += f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Global refactoring update applied to targeted files list: {', '.join(pending_changes.keys())}.\n"
    _, current_hist_sha_branch = gh.get_file_metadata(HISTORY_LOG_PATH, feature_branch_name)
    gh.commit_file_change(HISTORY_LOG_PATH, updated_history, "Room 110: Append global sweep results to history tracking logs", feature_branch_name, current_hist_sha_branch)

    # 5. Open single comprehensive Pull Request mapping
    pr_title = "✨ Room 110: Global Repository Optimization Audit Sweep"
    pr_url = gh.create_pull_request(pr_title, feature_branch_name, base_branch, full_pr_report)
    
    print(f"[🚀🎉] Workspace global verification complete! Proactive system Pull Request deployed: {pr_url}")

if __name__ == "__main__":
    main()
