import os
import sys
import json
import requests

def get_tech_context():
    """Fetches live architecture documentation from your website to preserve immutable context."""
    url = "https://www.bedrock.abrdns.com"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            print("[Room 110] Live architectural context pulled successfully from the documentation site.")
            return response.text[:8000]  # Chunked to fit token limits efficiently
    except Exception as e:
        print(f"[Room 110] Warning: Failed to connect to documentation site ({e}). Falling back to hardcoded rules.")
    
    return """
    Language: BedRock (.br), Core OS: Venilla OS.
    Core Philosophy: No Magic, Byte-Level Validation for MIPS. 
    Rule on Rdf: Differentiate strictly between Hardware Labels (physical direct addresses) and VRegs (dynamic pointer allocation).
    """

def query_gemini(prompt, api_key):
    """Invokes Gemini 1.5 Flash adaptively based on the key type (API Key vs Cloud Access Token)."""
    # Clean any accidental spaces or newlines from the key
    api_key = api_key.strip()
    
    # Mode 1: Standard AI Studio Key
    if api_key.startswith("AIzaSy"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    # Mode 2: Cloud Access Token (Starts with AQ. or other enterprise formats)
    else:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}' # Passing the AQ token securely in the headers
        }
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        data = res.json()
        
        if 'candidates' in data:
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"[Room 110] ❌ Gemini API Error Details: {json.dumps(data, indent=2)}")
            return None
            
    except Exception as e:
        print(f"[Room 110] ❌ Error querying Gemini: {e}")
        return None

def query_groq(prompt, api_key):
    """Invokes Llama 3 via Groq to act as the Devil's Advocate and review code for byte-level validation."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"[Room 110] Error querying Groq: {e}")
        return None

def main():
    print("[Room 110] Initiating autonomous compiler development loop...")
    
    # Securely retrieve tokens from environment variables
    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not gemini_key or not groq_key:
        print("[🔴 CRITICAL ERROR] API Keys are missing from GitHub Secrets! Add them to resume operation.")
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
    You are the Lead Software Architect of Room 110, dedicated to developing the BedRock Language Compiler.
    Here is the live immutable technical context of the project:
    ---
    {context}
    ---
    Here is the current compiler source code under inspection:
    ---
    {current_code}
    ---
    Task: Analyze the file and propose the next structural evolution for Code Generation or IR optimization. 
    Strictly adhere to 'No Magic' and 'Byte-Level Validation'. Provide clear code blocks.
    """

    print("[Room 110] Dispatching payload to Lead Architect (Gemini) for architectural solutions...")
    gemini_proposal = query_gemini(discussion_prompt, gemini_key)
    
    if gemini_proposal:
        print("[Room 110] Proposal acquired. Transitioning payload to Devil's Advocate (Groq/Llama) for strict review...")
        review_prompt = f"""
        You are the Architectural Reviewer and Devil's Advocate of Room 110.
        Review the proposed mutation written by the Lead Architect:
        {gemini_proposal}
        Cross-reference it with BedRock guidelines and bare-metal MIPS rules. Does this code break structural assumptions or use implicit 'magic'? Provide your final consensus report.
        """
        final_review = query_groq(review_prompt, groq_key)
        
        print("\n=== 🏛️ ROOM 110 CONSENSUS REPORT ===\n")
        print(final_review)
        print("\n====================================\n")
        print("[Room 110] Run completed successfully. GitHub will dispatch a notification summary to Chief Architect Karim.")
    else:
        print("[Room 110] Process aborted: Failed to fetch model responses.")

if __name__ == "__main__":
    main()
