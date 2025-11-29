"""
BAJAJ HEALTH DATATHON - Document Extraction System
CLI Script

This script processes a folder of invoices/bills and extracts data into JSON files.
It handles PDF conversion, OCR, and AI analysis.
"""
import os
import sys
import json
import base64
import time
import requests
import glob
import pytesseract
from PIL import Image
from dotenv import load_dotenv
import pypdf
import io

# Load environment variables
load_dotenv()

# Configuration
TESSERACT_CMD = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Set Tesseract path
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Set Poppler Path
POPPLER_PATH = r"C:\Program Files\poppler-25.11.0\Library\bin"
if os.path.exists(POPPLER_PATH):
    os.environ["PATH"] += os.pathsep + POPPLER_PATH
else:
    POPPLER_PATH_ALT = r"C:\Program Files\poppler-25.11.0\bin"
    if os.path.exists(POPPLER_PATH_ALT):
        os.environ["PATH"] += os.pathsep + POPPLER_PATH_ALT

def clean_json_string(json_str):
    """Clean AI output to get valid JSON"""
    json_str = json_str.replace("```json", "").replace("```", "")
    start = json_str.find("{")
    end = json_str.rfind("}")
    if start != -1 and end != -1:
        json_str = json_str[start:end+1]
    return json_str

def encode_pil_image(image):
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def extract_content(file_path):
    """Extract content for AI (Vision prioritized)"""
    print(f"🔍 Extracting content from {os.path.basename(file_path)}...")
    
    content = {
        "text": "",
        "page_count": 1,
        "images": [], # List of base64 images
        "extraction_method": "unknown"
    }
    
    try:
        if file_path.lower().endswith('.pdf'):
            # Try converting PDF to Images (Best for Vision)
            try:
                from pdf2image import convert_from_path
                print("   📸 Converting PDF pages to images...")
                pil_images = convert_from_path(file_path)
                content["page_count"] = len(pil_images)
                content["images"] = [encode_pil_image(img) for img in pil_images]
                content["extraction_method"] = "pdf_vision"
                
                # Also extract text as backup
                reader = pypdf.PdfReader(file_path)
                for i, page in enumerate(reader.pages):
                    content["text"] += f"\n--- PAGE {i+1} ---\n{page.extract_text()}"
                    
            except Exception as e:
                print(f"   ⚠️ PDF Vision failed: {e}")
                # Fallback: Text Only
                reader = pypdf.PdfReader(file_path)
                content["page_count"] = len(reader.pages)
                for i, page in enumerate(reader.pages):
                    content["text"] += f"\n--- PAGE {i+1} ---\n{page.extract_text()}"
                content["extraction_method"] = "pdf_text_only"
                
        else:
            # Image Processing
            print("   📸 Processing Image...")
            with open(file_path, "rb") as f:
                img_bytes = f.read()
                content["images"] = [base64.b64encode(img_bytes).decode('utf-8')]
            
            try:
                content["text"] = pytesseract.image_to_string(Image.open(file_path))
            except: pass
            content["extraction_method"] = "image_vision"
            
    except Exception as e:
        print(f"❌ Extraction Error: {e}")
        
    return content

# --- AI PROVIDERS & LOAD BALANCING ---

API_POOL = []
CURRENT_KEY_INDEX = 0

def load_api_keys():
    """Load all available API keys into a pool"""
    global API_POOL
    API_POOL = []
    
    # Helper to add keys
    def add_keys(prefix, provider_name):
        # Check base key
        key = os.getenv(f"{prefix}_API_KEY")
        if key: API_POOL.append({"provider": provider_name, "key": key})
        
        # Check numbered keys (1-10)
        for i in range(1, 11):
            key = os.getenv(f"{prefix}_API_KEY_{i}")
            if key: API_POOL.append({"provider": provider_name, "key": key})

    add_keys("GEMINI", "gemini")
    add_keys("OPENAI", "openai")
    add_keys("ANTHROPIC", "anthropic")
    
    if not API_POOL:
        print("❌ No API Keys found! Set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in .env")
        sys.exit(1)
        
    print(f"⚡ Loaded {len(API_POOL)} API Key(s) for Load Balancing")

# Initialize Pool
load_api_keys()

def get_next_provider():
    """Round-robin selection of API provider"""
    global CURRENT_KEY_INDEX
    if not API_POOL: return None
    
    provider = API_POOL[CURRENT_KEY_INDEX]
    CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(API_POOL)
    return provider

def get_common_prompt(filename, page_count):
    return f"""
    You are an expert Forensic Auditor. Analyze this document (Filename: {filename}, Pages: {page_count}).

    INSTRUCTIONS:
    1. **EXTRACTION**: Extract all visible data. If a Total is clearly the final amount to be paid, extract it.
    2. **PAGE MAPPING**: Assign items to their correct pages based on visual markers.
    3. **ANALYSIS**: Flag visual anomalies (edits, fonts) and duplicate items.

    TASK:
    1. Extract Header Info.
    2. Extract Line Items (Description, Qty, Unit Price, Amount).
    3. Extract Financial Totals (Subtotal, Tax, Total).

    OUTPUT JSON STRUCTURE:
    {{
        "file_info": {{
            "file_name": "{filename}",
            "page_count": {page_count},
            "document_type": "Invoice/Receipt/Bill/Statement",
            "document_title": "string",
            "printed_on": "string or null"
        }},
        "header": {{
            "id": "string",
            "date": "YYYY-MM-DD",
            "vendor_name": "string",
            "recipient_name": "string"
        }},
        "pages": [
            {{
                "page_number": 1,
                "line_items": [
                    {{"description": "string", "quantity": number, "unit_price": number, "amount": number}}
                ],
                "page_anomalies": ["list", "of", "visual", "issues"]
            }}
        ],
        "financials": {{
            "subtotal": number,
            "tax": number,
            "extracted_total": number
        }},
        "fraud_analysis": {{
            "risk_level": "LOW/MEDIUM/HIGH",
            "pixel_anomalies_detected": boolean,
            "duplicates_detected": boolean,
            "flags": ["list", "of", "issues"],
            "reasoning": "detailed explanation"
        }}
    }}
    """

def call_gemini(content, filename, api_key):
    print(f"🤖 Analyzing {filename} with Gemini 2.5 Flash (Key: ...{api_key[-4:]})...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    parts = [{"text": get_common_prompt(filename, content['page_count'])}]
    
    for i, img_b64 in enumerate(content["images"][:5]):
        parts.append({"text": f"--- VISUAL DATA FOR PAGE {i+1} ---"})
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": img_b64}})

    if content["text"]:
        parts.append({"text": f"EXTRACTED TEXT CONTEXT:\n{content['text']}"})

    # Retry Logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                url, headers={'Content-Type': 'application/json'},
                json={"contents": [{"parts": parts}]}, timeout=120
            )
            if response.status_code == 200:
                res_json = response.json()
                text = res_json['candidates'][0]['content']['parts'][0]['text']
                usage = res_json.get('usageMetadata', {})
                token_info = {
                    "prompt_tokens": usage.get('promptTokenCount', 0),
                    "output_tokens": usage.get('candidatesTokenCount', 0),
                    "total_tokens": usage.get('totalTokenCount', 0),
                    "model": "gemini-2.5-flash"
                }
                return text, token_info
            elif response.status_code == 429:
                print(f"   ⏳ Rate limit hit. Waiting 5s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(5)
            else:
                print(f"❌ Gemini Error: {response.text}")
                return None, None
        except Exception as e:
            print(f"   ⚠️ Request Failed: {e}. Retrying...")
            time.sleep(2)
            
    return None, None

def call_openai(content, filename, api_key):
    print(f"🤖 Analyzing {filename} with GPT-4o (Key: ...{api_key[-4:]})...")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        messages = [
            {"role": "system", "content": "You are a JSON-only extraction API."},
            {"role": "user", "content": []}
        ]
        
        user_content = messages[1]["content"]
        user_content.append({"type": "text", "text": get_common_prompt(filename, content['page_count'])})
        
        for i, img_b64 in enumerate(content["images"][:5]):
            user_content.append({"type": "text", "text": f"--- PAGE {i+1} ---"})
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
            })
            
        if content["text"]:
            user_content.append({"type": "text", "text": f"TEXT CONTEXT:\n{content['text']}"})

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=4000
        )
        
        text = response.choices[0].message.content
        usage = response.usage
        token_info = {
            "prompt_tokens": usage.prompt_tokens,
            "output_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "model": "gpt-4o"
        }
        return text, token_info
    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        return None, None

def call_anthropic(content, filename, api_key):
    print(f"🤖 Analyzing {filename} with Claude 3.5 Sonnet (Key: ...{api_key[-4:]})...")
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        message_content = []
        
        # Add Images
        for i, img_b64 in enumerate(content["images"][:5]):
            message_content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}
            })
            
        # Add Text Prompt
        prompt = get_common_prompt(filename, content['page_count'])
        if content["text"]:
            prompt += f"\n\nTEXT CONTEXT:\n{content['text']}"
            
        message_content.append({"type": "text", "text": prompt})

        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4000,
            messages=[{"role": "user", "content": message_content}]
        )
        
        text = response.content[0].text
        usage = response.usage
        token_info = {
            "prompt_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "total_tokens": usage.input_tokens + usage.output_tokens,
            "model": "claude-3-5-sonnet"
        }
        return text, token_info
    except Exception as e:
        print(f"❌ Anthropic Error: {e}")
        return None, None

def analyze_document(content, filename):
    """Route to available AI provider using Round-Robin"""
    provider_info = get_next_provider()
    
    if not provider_info:
        return None, None
        
    provider = provider_info["provider"]
    key = provider_info["key"]
    
    if provider == "gemini":
        return call_gemini(content, filename, key)
    elif provider == "openai":
        return call_openai(content, filename, key)
    elif provider == "anthropic":
        return call_anthropic(content, filename, key)
    
    return None, None

def validate_math(data):
    """Perform Python-side math validation"""
    try:
        calculated_total = 0.0
        line_items = []
        
        if "pages" in data:
            for page in data["pages"]:
                if "line_items" in page:
                    line_items.extend(page["line_items"])
        elif "line_items" in data:
            line_items = data["line_items"]
            
        for item in line_items:
            amount = item.get("amount")
            if amount is not None:
                try: calculated_total += float(amount)
                except: pass
                
        financials = data.get("financials", {})
        extracted_total = financials.get("extracted_total")
        
        is_match = None
        match_status = "UNKNOWN"
        
        if extracted_total is not None:
            try:
                extracted_total = float(extracted_total)
                if abs(extracted_total - calculated_total) < 0.10:
                    is_match = True
                    match_status = "MATCH"
                else:
                    is_match = False
                    match_status = "MISMATCH"
            except:
                match_status = "INVALID_TOTAL_FORMAT"
        else:
            match_status = "TOTAL_MISSING"

        financials["calculated_total"] = round(calculated_total, 2)
        financials["is_match"] = is_match
        data["financials"] = financials
        
        fraud = data.get("fraud_analysis", {})
        if is_match is False and extracted_total is not None:
            fraud["math_mismatch_detected"] = True
            msg = f"Math mismatch: Extracted {extracted_total} vs Calculated {round(calculated_total, 2)}"
            if msg not in fraud.get("flags", []):
                fraud.setdefault("flags", []).append(msg)
            if abs(extracted_total - calculated_total) > 1.0:
                 if fraud.get("risk_level") == "LOW":
                     fraud["risk_level"] = "MEDIUM"
        else:
            fraud["math_mismatch_detected"] = False
            
        data["fraud_analysis"] = fraud
        return data, match_status
        
    except Exception as e:
        print(f"   ⚠️ Validation Error: {e}")
        return data, "ERROR"

def process_file(file_path):
    print(f"\n🚀 Processing: {file_path}")
    content = extract_content(file_path)
    
    if not content["text"].strip() and not content["images"]:
        print("   ❌ No content found")
        return False

    json_str, token_info = analyze_document(content, os.path.basename(file_path))
    
    if json_str:
        json_str = clean_json_string(json_str)
        try:
            data = json.loads(json_str)
            
            # Inject Token Info at the top
            if token_info:
                data = {"token_usage": token_info, **data}
                
            data, match_status = validate_math(data)
            
            output_file = f"result_{os.path.basename(file_path)}.json"
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)
            print(f"   ✅ Saved to {output_file}")
            print(f"   🛡️ Risk: {data.get('fraud_analysis', {}).get('risk_level', 'UNKNOWN')}")
            print(f"   💰 Math Validation: {match_status}")
            if token_info:
                print(f"   🔢 Tokens: {token_info['total_tokens']} ({token_info['model']})")
            return True
            
        except json.JSONDecodeError:
            print("   ❌ Invalid JSON from AI")
            return False
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python submit_bill.py <file_or_directory>")
        return

    inputs = sys.argv[1:]
    files_to_process = []

    for inp in inputs:
        if os.path.isdir(inp):
            for ext in ['*.pdf', '*.jpg', '*.jpeg', '*.png']:
                files_to_process.extend(glob.glob(os.path.join(inp, ext)))
        elif os.path.exists(inp):
            files_to_process.append(inp)

    if not files_to_process:
        print("❌ No files found")
        return

    print(f"📦 Found {len(files_to_process)} files...")
    failed_files = []

    # 1. First Pass
    for i, f in enumerate(files_to_process):
        print(f"\n--- File {i+1}/{len(files_to_process)} ---")
        success = process_file(f)
        if not success:
            failed_files.append(f)
        
        # Safety Delay
        if i < len(files_to_process) - 1:
            print("   ⏳ Waiting 2s before next file...")
            time.sleep(2)

    # 2. Retry Failed Files
    if failed_files:
        print(f"\n\n⚠️ Retrying {len(failed_files)} failed files...")
        time.sleep(5) # Cool down before retrying
        
        for i, f in enumerate(failed_files):
            print(f"\n--- Retry {i+1}/{len(failed_files)}: {f} ---")
            process_file(f)
            time.sleep(3)

    print("\n✅ Batch Processing Complete!")

if __name__ == "__main__":
    main()
