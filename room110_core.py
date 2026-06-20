# -*- coding: utf-8 -*-
"""
غرفة 110: وكيل إعادة الهيكلة التلقائي والمستقل لمشروع BedRock (معمارية MIPS)
يعمل هذا السكربت بالكامل داخل بيئة GitHub Actions دون أي اعتمادات خارجية على subprocess CLI.
"""

import os
import re
import sys
import time
import json
import base64
import requests

# ==========================================
# الإعدادات والثوابت العامة
# ==========================================
BEDROCK_RULES_URL = "https://bedrock.abrdns.com"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
TARGET_FILE_PATH = "src/mips.rs"
HISTORY_LOG_PATH = "refactor_history.log"

# القواعد الاحتياطية في حال فشل الاتصال بالموقع
FALLBACK_RULES = """
Rule 1: Strict MIPS byte-level and alignment validation.
Rule 2: Eliminate redundant register allocations and optimize branch delays.
Rule 3: Ensure absolute type safety inside the BedRock compiler backend IR.
Rule 4: Output pure Rust syntax exclusively bounded inside a single ```rust block.
"""

# ==========================================
# الموجهات الصارمة لمنع الهلوسة البرمجية
# ==========================================
PROPOSAL_SYSTEM_PROMPT = """
You are the Lead Proposal Agent for the BedRock Compiler Backend Engineering Council.
Your sole domain of expertise is compiler optimization, MIPS instruction set architectures, and Rust language implementations.

CRITICAL DIRECTIVES:
1. You MUST operate strictly within the boundaries of a MIPS backend compiler. Do NOT hallucinate unrelated features.
2. Analyze the current source code against the provided BedRock language specs. Identify technical debt, optimization bottlenecks, or safety violations.
3. If no optimization is required, you must reply with exactly "NO_CHANGES_REQUIRED".
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
# وظائف الاتصال والتحقق من الأخطاء
# ==========================================
def fetch_bedrock_rules() -> str:
    """جلب قواعد لغة BedRock من الموقع الرسمي مع تفعيل آلية اتصال احتياطية"""
    print("[🔄] جاري جلب قواعد BedRock من الموقع الرسمي...")
    try:
        response = requests.get(BEDROCK_RULES_URL, timeout=12)
        if response.status_code == 200 and response.text.strip():
            print("[✅] تم تحميل قواعد لغة BedRock بنجاح.")
            return response.text
        else:
            print(f"[⚠️] استجابة غير متوقعة {response.status_code}. سيتم استخدام القواعد الاحتياطية.")
            return FALLBACK_RULES
    except Exception as e:
        print(f"[⚠️] فشل الاتصال بالخادم ({str(e)}). سيتم استخدام القواعد الاحتياطية.")
        return FALLBACK_RULES

def safe_groq_api_call(headers: dict, payload: dict) -> str:
    """إرسال طلبات آمنة لـ Groq API مع فحص دقيق للبيانات المستلمة لمنع أي KeyError"""
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=45)
    except Exception as e:
        print(f"[🔴] خطأ في الاتصال بالشبكة مع Groq API: {str(e)}")
        sys.exit(1)
        
    if response.status_code != 200:
        print(f"[🔴] فشل طلب Groq API برمز حالة: {response.status_code}")
        print(f"[🔴] الرد الخام المستلم من الخادم:\n{response.text}")
        sys.exit(1)
        
    try:
        data = response.json()
    except Exception as e:
        print(f"[🔴] فشل في تحليل رد الـ JSON المستلم: {str(e)}")
        print(f"[🔴] البيانات الخام:\n{response.text}")
        sys.exit(1)
        
    if 'choices' not in data or not data['choices']:
        print("[🔴] بنية غير صالحة: حقل 'choices' مفقود أو فارغ في رد Groq API.")
        print(f"[🔴] الرد الكامل:\n{json.dumps(data, indent=2)}")
        sys.exit(1)
        
    return data['choices'][0]['message']['content']

# ==========================================
# حلقة النقاش واتخاذ القرار (Council Debate)
# ==========================================
def run_council_debate(current_code: str, rules: str, groq_key: str) -> tuple:
    """تنسيق حلقة نقاش ذكية بين خبير الاقتراحات ومراجع الجودة"""
    if not groq_key:
        print("[🔴] خطأ في البيئة: مفتاح 'GROQ_API_KEY' غير متوفر.")
        sys.exit(1)
        
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    
    # 1. خبير الاقتراحات يفحص الكود الحالي
    print("[🤖 خبير 1] جاري فحص ملف MIPS والبحث عن ديون تقنية...")
    proposal_prompt = f"""
    Rules:
    {rules}
    
    Current Code in '{TARGET_FILE_PATH}':
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
    
    if "NO_CHANGES_REQUIRED" in proposal_output:
        print("[✅] قرر مجلس الخبراء أن الكود الحالي مثالي ومستقر تماماً.")
        return None, ""
        
    print("[🤖 خبير 1] تم تقديم اقتراح لتحسين الأداء وهيكلة الكود.")
    
    # 2. خبير المراجعة يدقق في الاقتراح ويصيغ الكود النهائي للـ Compiler
    print("[🤖 خبير 2] جاري مراجعة وتدقيق الاقتراح المقدم للتأكد من الملاءمة الصارمة...")
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
    print("[✅] تم التوصل إلى اتفاق نهائي ومصادقة الكود بنجاح.")
    
    # صياغة تقرير الخبراء ليوضع في الـ Pull Request
    full_report_body = f"""### 🏛️ تقرير مجلس خبراء الغرفة 110 (Room 110 Council)

تم إجراء تدقيق استباقي ومقارنة الكود الحالي مع معايير لغة **BedRock**.

#### 🔍 المرحلة الأولى: تشخيص خبير الاقتراحات (Proposal)
{proposal_output}

#### 🛠️ المرحلة الثانية: قرار ومراجعة خبير الجودة والتوافق (Reviewer)
{final_consensus}
"""
    return final_consensus, full_report_body

# ==========================================
# التعامل المباشر مع واجهة GitHub REST API
# ==========================================
class GitHubNativeClient:
    """عميل تفاعل مباشر مع GitHub REST API بدون استخدام subprocess"""
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.base_url = f"[https://api.github.com/repos/](https://api.github.com/repos/){repo}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
    def check_response_status(self, response, task_name: str):
        if response.status_code not in [200, 201, 202, 204]:
            print(f"[🔴] فشل إجراء GitHub API أثناء: {task_name}")
            print(f"[🔴] رمز الاستجابة: {response.status_code}")
            print(f"[🔴] تفاصيل الرد:\n{response.text}")
            sys.exit(1)

    def get_default_branch(self) -> str:
        res = requests.get(self.base_url, headers=self.headers)
        self.check_response_status(res, "جلب معلومات المستودع الأساسية")
        return res.json().get("default_branch", "main")

    def get_branch_sha(self, branch: str) -> str:
        url = f"{self.base_url}/git/ref/heads/{branch}"
        res = requests.get(url, headers=self.headers)
        self.check_response_status(res, f"جلب SHA للفرع {branch}")
        return res.json()["object"]["sha"]

    def create_new_branch(self, new_branch_name: str, base_sha: str):
        url = f"{self.base_url}/git/refs"
        payload = {
            "ref": f"refs/heads/{new_branch_name}",
            "sha": base_sha
        }
        print(f"[🐙] جاري إنشاء فرع مخصص بعيد: {new_branch_name}...")
        res = requests.post(url, headers=self.headers, json=payload)
        self.check_response_status(res, f"إنشاء الفرع الجديد {new_branch_name}")

    def get_file_metadata(self, path: str, branch: str) -> tuple:
        """جلب محتوى الملف وبيانات SHA الخاصة به"""
        url = f"{self.base_url}/contents/{path}?ref={branch}"
        res = requests.get(url, headers=self.headers)
        if res.status_code == 404:
            return None, None
        self.check_response_status(res, f"تحميل بيانات الملف {path}")
        data = res.json()
        content_decoded = base64.b64decode(data["content"]).decode("utf-8")
        return content_decoded, data["sha"]

    def commit_file_change(self, path: str, content: str, commit_message: str, branch: str, sha: str = None):
        """عمل Commit وتحديث للملف مباشرة على الـ Branch"""
        url = f"{self.base_url}/contents/{path}"
        content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": commit_message,
            "content": content_b64,
            "branch": branch
        }
        if sha:
            payload["sha"] = sha
            
        print(f"[🐙] جاري حفظ التغييرات وتطبيق Commit للملف '{path}' على الفرع '{branch}'...")
        res = requests.put(url, headers=self.headers, json=payload)
        self.check_response_status(res, f"تنفيذ Commit للملف {path}")

    def create_pull_request(self, title: str, head_branch: str, base_branch: str, body: str) -> str:
        """إنشاء طلب دمج (Pull Request) بربط مباشر"""
        url = f"{self.base_url}/pulls"
        payload = {
            "title": title,
            "head": head_branch,
            "base": base_branch,
            "body": body
        }
        print(f"[🐙] جاري إرسال طلب الدمج (Pull Request) من '{head_branch}' إلى '{base_branch}'...")
        res = requests.post(url, headers=self.headers, json=payload)
        self.check_response_status(res, "إنشاء طلب الدمج")
        return res.json().get("html_url", "")

    def check_merged_pull_requests(self, base_branch: str) -> list:
        """جلب طلبات الدمج المكتملة مؤخراً للتعلم منها"""
        url = f"{self.base_url}/pulls?state=closed&base={base_branch}&sort=updated&direction=desc&per_page=10"
        res = requests.get(url, headers=self.headers)
        self.check_response_status(res, "مراجعة أرشيف طلبات الدمج")
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
# دورة التنفيذ الأساسية للوكيل المستقل
# ==========================================
def main():
    print("[🚀] تفعيل نظام الوكيل الذكي للغرفة 110 لإعادة الهيكلة والتطوير...")
    
    # التحقق من متغيرات البيئة الأساسية في GitHub Runner
    gh_token = os.getenv("GITHUB_TOKEN")
    gh_repo = os.getenv("GITHUB_REPOSITORY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not gh_token or not gh_repo:
        print("[🔴] خطأ إداري: متغيرات البيئة GITHUB_TOKEN أو GITHUB_REPOSITORY مفقودة.")
        sys.exit(1)
        
    gh = GitHubNativeClient(gh_token, gh_repo)
    
    # 1. جلب شروط وقواعد لغة BedRock
    rules = fetch_bedrock_rules()
    
    # 2. تحديد الفرع الافتراضي وجلب الكود المستهدف الحالي
    base_branch = gh.get_default_branch()
    print(f"[⚙️] الفرع الافتراضي للمستودع هو: {base_branch}")
    
    current_code, target_file_sha = gh.get_file_metadata(TARGET_FILE_PATH, base_branch)
    if current_code is None:
        print(f"[⚠️] المسار '{TARGET_FILE_PATH}' غير موجود على الفرع الأساسي. سيتم إنشاء الملف الجديد.")
        current_code = ""
    
    # 3. محرك التعلم الذاتي والتفاعل الاستباقي (Self-Learning)
    print("[🧠] جاري فحص طلبات الدمج المكتملة للتعلم من تاريخ التطوير...")
    merged_prs = gh.check_merged_pull_requests(base_branch)
    
    history_content, history_sha = gh.get_file_metadata(HISTORY_LOG_PATH, base_branch)
    if history_content is None:
        history_content = "=== سجلات تاريخ التعلم الذاتي للغرفة 110 ===\n"
        
    updated_history = history_content
    learnings_found = False
    
    for pr in merged_prs:
        pr_identifier = f"PR #{pr['number']}"
        if pr_identifier not in updated_history:
            print(f"[💡] تم رصد دمج سابق ({pr_identifier} - {pr['title']}). جاري إدماجه في قاعدة المعرفة المكتسبة...")
            updated_history += f"\n[{pr['merged_at']}] تعلم من الدمج المكتمل لـ {pr_identifier}: عنوان: {pr['title']}.\n"
            learnings_found = True
            
    # 4. بدء حلقة النقاش واتخاذ القرار
    consensus_code_raw, full_report_body = run_council_debate(current_code, rules, groq_key)
    
    if not consensus_code_raw:
        # الكود حالياً في أفضل حالاته ولا يتطلب تعديلاً
        if learnings_found:
            print("[📝] جاري حفظ بيانات التعلم المكتسبة في ملف السجل التاريخي...")
            gh.commit_file_change(HISTORY_LOG_PATH, updated_history, "Room 110: Update intelligence and learnings history [skip ci]", base_branch, history_sha)
        return

    # استخراج كود الـ Rust النظيف من رد الخبير بذكاء
    code_match = re.search(r"```rust\s*\n(.*?)\n```", consensus_code_raw, re.DOTALL | re.IGNORECASE)
    if not code_match:
        print("[🔴] خطأ في معالجة المخرجات: لم يتم العثور على كتل كود Rust برمجية صحيحة في مخرجات المجلس.")
        print(f"[🔴] المخرجات المستلمة بالكامل:\n{consensus_code_raw}")
        sys.exit(1)
        
    optimized_code = code_match.group(1).strip()
    
    # التحقق للتأكد من أن التعديل المقترح حقيقي وليس وهمياً أو مطابقاً للكود الحالي
    if current_code.strip() == optimized_code:
        print("[🎉] الكود المقترح متطابق تماماً مع الكود الحالي. لا توجد حاجة للتعديل.")
        if learnings_found:
            print("[📝] جاري حفظ السجلات الجديدة فقط...")
            gh.commit_file_change(HISTORY_LOG_PATH, updated_history, "Room 110: Update intelligence log [skip ci]", base_branch, history_sha)
        return

    print("[🔥] تم اكتشاف فرص لتحسين وتعديل الكود البرمجي للمترجم!")
    
    # 5. التحديث وبدء تطبيق التعديلات بشكل آمن برمجياً
    timestamp = int(time.time())
    feature_branch_name = f"refactor/room110-{timestamp}"
    
    base_sha = gh.get_branch_sha(base_branch)
    gh.create_new_branch(feature_branch_name, base_sha)
    
    # كتابة ملف كود Rust الجديد على الفرع المنشأ حديثاً
    gh.commit_file_change(TARGET_FILE_PATH, optimized_code, "Room 110: Optimization sweep by engineering council", feature_branch_name, target_file_sha)
    
    # تحديث ملف التعلم الذاتي وحفظه على نفس الفرع
    updated_history += f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] تم اقتراح إعادة هيكلة وتحديث الكود لملف {TARGET_FILE_PATH}.\n"
    _, current_hist_sha_branch = gh.get_file_metadata(HISTORY_LOG_PATH, feature_branch_name)
    gh.commit_file_change(HISTORY_LOG_PATH, updated_history, "Room 110: Record execution to refactor history log", feature_branch_name, current_hist_sha_branch)

    # 6. إرسال وفتح الـ Pull Request النهائي مع وضع تقرير الخبراء المجمع
    pr_title = f"✨ Room 110 [Proactive Refactor]: Optimization Sweep for {TARGET_FILE_PATH}"
    pr_url = gh.create_pull_request(pr_title, feature_branch_name, base_branch, full_report_body)
    
    print(f"[🚀🎉] تم الانتهاء بنجاح! تم فتح طلب دمج استباقي جديد: {pr_url}")

if __name__ == "__main__":
    main()
