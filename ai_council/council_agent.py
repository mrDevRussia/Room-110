import os
import json
import requests
import re

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def call_openrouter(model_name, system_prompt, user_prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "BedRock AI Council"
    }
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling model {model_name}: {e}")
        return ""

def main():
    print("Loading project context...")
    if not os.path.exists("project_context.md"):
        print("Context file missing!")
        return

    with open("project_context.md", "r", encoding="utf-8") as f:
        repo_context = f.read()

    # Step 1: Gemini determines the scale of implementation and gives classification
    print("Agent 1 (Gemini) is evaluating the codebase...")
    gemini_system = (
        "You are the Chief Software Architect of the BedRock Compiler project. "
        "Analyze the context and propose ONE highly stable improvement or fix. "
        "CRITICAL: You must classify this change at the very first line of your response. "
        "Use exactly 'CLASSIFICATION: MINOR' for simple optimization, bug fixes, or refactoring. "
        "Use exactly 'CLASSIFICATION: MAJOR' for architectural adjustments, parser changes, or adding a new CPU target/architecture."
    )
    gemini_user = f"Review the codebase and generate your classified proposal:\n\n{repo_context}"
    
    proposal = call_openrouter("google/gemini-2.5-flash:free", gemini_system, gemini_user)
    if not proposal: return
    print(f"\n--- Architect Proposal ---\n{proposal}\n")

    # Determine classification path
    is_major = "CLASSIFICATION: MAJOR" in proposal
    change_type = "MAJOR" if is_major else "MINOR"
    print(f"Detected Change Strategy Type: {change_type}")

    # Step 2: Qwen writes the actual code
    print("Agent 2 (Qwen) is generating implementation code...")
    qwen_system = "You are an elite systems engineer. Implement the architectural proposal perfectly. Output file paths and code contents within markdown code blocks. Always prefix files with '### File: path/to/file.ext'."  
    qwen_user = f"Implement this proposal:\n{proposal}\n\nInside this context:\n{repo_context}"
    
    engineered_code = call_openrouter("qwen/qwen-2.5-72b-instruct:free", qwen_system, qwen_user)
    if not engineered_code: return

    # Step 3: Llama reviews the system logic
    print("Agent 3 (Llama) is auditing the code...")
    llama_system = "You are a rigid security auditor. If the code is stable and error-free, reply with 'APPROVED' followed by file updates. If risky, reply 'REJECTED'."
    llama_user = f"Audit this code:\n{engineered_code}\n\nAgainst this proposal:\n{proposal}"
    
    critique = call_openrouter("meta-llama/llama-3.3-70b-instruct:free", llama_system, llama_user)
    if not critique: return

    if "APPROVED" in critique.upper():
        print("Council consensus reached. Writing changes to execution layout...")
        code_blocks = re.findall(r'### File:\s*([^\n]+)\n```[^\n]*\n(.*?)```', engineered_code, re.DOTALL)
        
        if not code_blocks:
            code_blocks = re.findall(r'### File:\s*([^\n]+)\n```[^\n]*\n(.*?)```', critique, re.DOTALL)

        if code_blocks:
            for file_path, code_content in code_blocks:
                file_path = file_path.strip()
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code_content.strip())
                print(f"Updated: {file_path}")
            
            # Write the decision tag for GitHub Actions workflow to parse
            with open("action_trigger.txt", "w") as f:
                f.write(change_type)
        else:
            print("Failed to parse output code blocks.")
    else:
        print("Council rejected the solution.")

if __name__ == "__main__":
    main()
