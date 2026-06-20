import os
import sys
import json
import requests

def get_tech_context():
    """Fetches live architecture documentation from your website."""
    url = "https://www.bedrock.abrdns.com"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            print("[Room 110] Live architectural context pulled successfully.")
            return response.text[:8000]
    except Exception as e:
        print(f"[Room 110] Warning: Falling back to hardcoded rules.")
    
    return """
    Language: BedRock (.br), Core OS: Venilla OS.
    Core Philosophy: No Magic, Byte-Level Validation for MIPS. 
    Rule on Rdf: Differentiate strictly between Hardware Labels (physical direct addresses) and VRegs (dynamic pointer allocation).
    """

def query_groq(prompt, model_name, api_key):
    """Invokes Groq dynamically with the specified model."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        data = res.json()
        if 'choices' in data:
            return data['choices'][0]['message']['content']
        else:
            print(f"[Room 110] ❌ Groq Error Details: {json.dumps(data, indent=2)}")
            return None
    except Exception as e:
        print(f"[Room 110] ❌ Error querying Groq: {e}")
        return None

def main():
    print("[Room 110] Initiating autonomous compiler development loop via Groq Architecture...")
    
    # Retrieve only Groq Key now
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("[🔴 CRITICAL ERROR] GROQ_API_KEY is missing from GitHub Secrets!")
        sys.exit(1)
        
    context = get_tech_context()
    
    # Locate the active compiler target
    target_file = "src/mips.rs" if os.path.exists("src/mips.rs") else "mips.rs"
    current_code = ""
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            current_code = f.read()
    else:
        current_code = "// BedRock Compiler source file not found or initializing."

    discussion_prompt = f"""
    You are the Lead Software Architect of Room 110, developing the BedRock Language Compiler.
    Context: {context}
    Current Code: {current_code}
    Task: Propose the next logical development step or bug fix for the MIPS backend. Adhere to 'No Magic'.
    """

    print("[Room 110] Dispatching payload to Lead Architect (Llama-3-70B)...")
    proposal = query_groq(discussion_prompt, "llama3-70b-8192", groq_key)
    
    if proposal:
        print("[Room 110] Proposal acquired. Transitioning to Devil's Advocate (Llama-3-8B) for strict review...")
        review_prompt = f"""
        Review this proposed compiler mutation for BedRock:
        {proposal}
        Does this code break bare-metal MIPS validation or use implicit 'magic'? Provide the final consensus report.
        """
        final_review = query_groq(review_prompt, "llama3-8b-8192", groq_key)
        
        print("\n=== 🏛️ ROOM 110 CONSENSUS REPORT ===\n")
        print(final_review)
        print("\n====================================\n")
        print("[Room 110] Run completed successfully.")
    else:
        print("[Room 110] Process aborted: Failed to fetch model responses.")

if __name__ == "__main__":
    main()
