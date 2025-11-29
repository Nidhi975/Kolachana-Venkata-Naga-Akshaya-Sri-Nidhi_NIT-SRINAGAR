# 📄 Bill & Invoice Data Extractor

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A tool that uses AI to read bills and invoices, pull out important information, and check for possible fraud or errors.

## 📋 What's Inside

- [What This Does](#what-this-does)
- [Main Features](#main-features)
- [How It Works](#how-it-works)
- [Getting Started](#getting-started)
- [Settings](#settings)
- [How to Use](#how-to-use)
- [API Guide](#api-guide)
- [Output Data](#output-data)
- [Fraud Checking](#fraud-checking)
- [Using Multiple APIs](#using-multiple-apis)
- [Docker Setup](#docker-setup)
- [Testing](#testing)
- [Tech Info](#tech-info)
- [Common Problems](#common-problems)
- [Contributing](#contributing)

---

## 🎯 What This Does

This tool helps you automatically extract data from medical bills, invoices, and receipts. Instead of manually typing everything, just upload your document and get back organized JSON data.

**What it handles:**
- Reading PDF and image files (JPG, PNG)
- Pulling out line items, prices, and dates
- Checking if the math adds up
- Looking for signs of tampering
- Working with Google Gemini, OpenAI, or Claude
- Processing lots of files at once

---

## ✨ Main Features

### 🤖 Works with Multiple AI Services

- Can use Google Gemini, OpenAI GPT-4, or Anthropic Claude
- Switches between them automatically if one is busy
- Turns PDF pages into images for better accuracy
- Falls back to text reading if images don't work
- Can handle multiple API keys to work faster

### 🔍 Checks for Problems in 5 Ways

1. **Image Check**: Looks for white-out, erasing, or photo editing
2. **Font Check**: Spots when text looks inconsistent
3. **Number Patterns**: Uses math to find suspicious numbers
4. **Duplicate Check**: Finds the same charge listed twice
5. **Math Check**: Makes sure line items add up to the total

### 📊 Handles Documents

- Works with PDF, JPG, and PNG files
- Can process long documents (over 100 pages)
- Remembers which page each item came from
- Figures out if it's an invoice, receipt, or bill

### 🏗️ User Friendly

- Run from command line or as a web service
- Process one file or a whole folder
- Track progress of ongoing jobs
- Retries automatically if something fails
- Shows how much the API calls cost

---

## 🏛️ How It Works

```
Step 1: You upload a PDF or image
         ↓
Step 2: System converts PDF to images (if needed)
        and reads any text it can find
         ↓
Step 3: Sends to AI service (Gemini, GPT-4, or Claude)
        AI looks at the image and extracts data
         ↓
Step 4: System checks everything
        - Adds up all line items
        - Compares to total shown on document
        - Looks for duplicate charges
        - Checks for signs of tampering
         ↓
Step 5: Returns clean JSON with:
        - All line items
        - Invoice info (date, vendor, etc.)
        - Money totals
        - Fraud risk score
```

---

## 🚀 Getting Started

### What You'll Need

- Python 3.10 or newer
- Tesseract OCR (helps read text from images)
- Poppler (helps convert PDFs to images)
- API key from Google, OpenAI, or Anthropic (at least one)

### Installation Steps

**Step 1: Download the code**
```bash
git clone <your-github-link>
cd akka
```

**Step 2: Install Python packages**
```bash
pip install -r requirements.txt
```

**Step 3: Install additional tools**

**For Windows:**
- Get Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
  - Install to: `C:\Program Files\Tesseract-OCR\`
- Get Poppler from: https://github.com/oschwartz10612/poppler-windows/releases
  - Extract to: `C:\Program Files\poppler-25.11.0\`

**For Mac:**
```bash
brew install tesseract
brew install poppler
```

**For Linux:**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install poppler-utils
```

**Step 4: Set up your API keys**

Make a copy of the settings file:
```bash
cp .env.template .env
```

Open `.env` in a text editor and add your key (need at least one):
```
GEMINI_API_KEY=paste_your_key_here
OPENAI_API_KEY=paste_your_key_here
ANTHROPIC_API_KEY=paste_your_key_here
```

---

## ⚙️ Settings

You can adjust settings in the `.env` file:

**API Keys:**
```
# Basic setup (pick at least one)
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Optional: Add more to go faster
GEMINI_API_KEY_1=extra_key
GEMINI_API_KEY_2=another_key
```

**File Limits:**
```
MAX_FILE_SIZE_MB=50        # Largest file size allowed
MAX_PAGES=100              # Most pages per document
```

**Fraud Detection:**
```
BENFORD_CHI_SQUARE_THRESHOLD=15.507    # Math test for fake numbers
FONT_OUTLIER_THRESHOLD=0.15            # How strict about fonts
TAMPERING_SENSITIVITY=0.7              # How strict about edits
```

**Server Options:**
```
API_HOST=0.0.0.0          # Server address
API_PORT=8000             # Port number
```

---

## 📖 How to Use

### Method 1: Command Line

Process files from your terminal:

```bash
# Single file
python submit_bill.py invoice.pdf

# Multiple files at once
python submit_bill.py invoice1.pdf bill2.jpg receipt3.png

# All files in a folder
python submit_bill.py "C:\path\to\your\invoices"
```

**What you get:**
- A JSON file for each document (`result_filename.json`)
- Summary in the terminal
- Info about whether math checks out
- Fraud risk level
- API token usage

### Method 2: Web Service

Start the server:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser and go to: **http://localhost:8000/docs**

You'll see an interactive page where you can upload files.

### Method 3: Batch Upload via API

Send multiple files at once:
```bash
curl -X POST "http://localhost:8000/api/v1/batch-extract" \
  -F "files=@invoice1.pdf" \
  -F "files=@invoice2.pdf" \
  -F "files=@receipt.jpg"
```

Check on your job:
```bash
curl "http://localhost:8000/api/v1/status/<job_id>"
```

---

## 📡 API Guide

### Upload One File
**Endpoint:** `POST /api/v1/extract`

Send a single file:
```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
  -F "file=@invoice.pdf"
```

You'll get back:
```json
{
  "job_id": "abc123...",
  "status_url": "/api/v1/status/abc123..."
}
```

### Upload Multiple Files
**Endpoint:** `POST /api/v1/batch-extract`

Send many files:
```bash
curl -X POST "http://localhost:8000/api/v1/batch-extract" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.jpg"
```

### Check Progress
**Endpoint:** `GET /api/v1/status/{job_id}`

See how it's going:

**Still working:**
```json
{
  "status": "processing",
  "progress": 50,
  "message": "Analyzing with AI"
}
```

**Done:**
```json
{
  "status": "completed",
  "progress": 100,
  "result": { /* all your data */ }
}
```

**Failed:**
```json
{
  "status": "failed",
  "error": "Something went wrong"
}
```

---

## 📄 Output Data

Here's what the JSON looks like:

```json
{
  "token_usage": {
    "total_tokens": 6655,
    "model": "gemini-2.5-flash"
  },
  "file_info": {
    "file_name": "invoice.pdf",
    "page_count": 2,
    "document_type": "Invoice"
  },
  "header": {
    "id": "INV-2025-001",
    "date": "2025-11-29",
    "vendor_name": "City Hospital",
    "recipient_name": "John Doe"
  },
  "pages": [
    {
      "page_number": 1,
      "line_items": [
        {
          "description": "Doctor Visit",
          "quantity": 1,
          "unit_price": 500,
          "amount": 500
        }
      ],
      "page_anomalies": []
    }
  ],
  "financials": {
    "subtotal": 4100,
    "tax": 0,
    "extracted_total": 4100,
    "calculated_total": 4100,
    "is_match": true
  },
  "fraud_analysis": {
    "risk_level": "LOW",
    "pixel_anomalies_detected": false,
    "duplicates_detected": false,
    "math_mismatch_detected": false,
    "flags": [],
    "reasoning": "Everything looks fine"
  }
}
```

**What each section means:**

- **token_usage** - Cost info for the API call
- **file_info** - Basic document details
- **header** - Invoice number, date, who sent it
- **pages** - Items listed on each page
- **financials** - Money totals and whether they match
- **fraud_analysis** - Risk score and problems found

---

## 🛡️ Fraud Checking

The system checks documents in 5 different ways:

### 1. Image Analysis
Looks at pixels to find:
- White-out or correction fluid
- Erased areas
- Photo editing marks

### 2. Font Consistency
Makes sure text looks uniform:
- Groups text by size and style
- Finds mismatched fonts
- Warns if over 15% looks different

### 3. Number Pattern Test (Benford's Law)
Natural financial data follows a pattern - numbers starting with 1 appear most often. Fake data doesn't follow this.

The system runs a math test. If the score goes over 15.507, it's suspicious.

### 4. Duplicate Detection
Looks for the same charge appearing twice:
- Compares descriptions and amounts
- Checks across all pages
- Flags exact matches

### 5. Math Verification
Adds everything up:
- Sums all line items
- Compares to document total
- Allows tiny differences (rounding)
- Warns if off by more than 1%

**Risk Levels:**
- **LOW** - No problems found
- **MEDIUM** - One or two small issues
- **HIGH** - Multiple red flags (needs review)

---

## 🔄 Using Multiple APIs

The system can juggle different AI services automatically.

**How it works:**
1. Add API keys to your `.env` file
2. System loads them all at startup
3. Each file uses the next service in line
4. Spreads out the work and avoids limits

**Setting up multiple keys:**
```
# Mix different services
GEMINI_API_KEY=google_key
OPENAI_API_KEY=openai_key
ANTHROPIC_API_KEY=claude_key

# Or add extras for one service
GEMINI_API_KEY_1=another_google_key
GEMINI_API_KEY_2=yet_another_one
```

**Processing flow:**
```
File 1 → Gemini
File 2 → OpenAI  
File 3 → Claude
File 4 → Back to Gemini
...and so on
```

**Safety features:**
- 2 second pause between files
- 5 second wait if rate limit hit
- Tries up to 3 times if it fails
- Retries all failed files at the end

---

## 🐳 Docker Setup

**Build the image:**
```bash
docker build -t bill-extractor:latest .
```

**Run it:**
```bash
docker run -d \
  --name bill-api \
  -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -v $(pwd)/outputs:/app/outputs \
  bill-extractor:latest
```

**Using docker-compose:**

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./outputs:/app/outputs
    restart: unless-stopped
```

Start:
```bash
docker-compose up -d
```

---

## 🧪 Testing

**Make a test bill:**
```bash
python create_test_bill.py
```

This creates `test_bill.jpg` - a fake invoice to test with.

**Try it out:**
```bash
# Command line
python submit_bill.py test_bill.jpg

# Or with API
curl -X POST "http://localhost:8000/api/v1/extract" \
  -F "file=@test_bill.jpg"
```

**Look at results:**
```bash
cat result_test_bill.jpg.json
```

---

## 🔧 Tech Info

**Python packages used:**
- `fastapi` - Web framework for API
- `uvicorn` - Runs the server
- `pytesseract` - Reads text from images
- `pdf2image` - Converts PDFs to images
- `Pillow` - Image processing
- `pypdf` - Gets text from PDFs
- `google-generativeai` - Google Gemini
- `openai` - GPT-4
- `anthropic` - Claude
- `python-dotenv` - Handles settings
- `requests` - Makes web calls

**Computer requirements:**
- CPU: 2 cores minimum (4+ better)
- RAM: 4 GB minimum (8+ better)
- Storage: 10 GB free space
- Python: 3.10 or newer

**Speed estimates:**
- One page: 3-8 seconds
- Five pages: 15-30 seconds
- Ten files: 2-4 minutes

**Accuracy rates:**
- Text reading: over 95%
- Financial data: over 98%
- Fraud detection: around 90%

**API costs per page (approximate):**
- Gemini: 1,000-2,000 tokens
- GPT-4: 1,500-3,000 tokens
- Claude: 1,200-2,500 tokens

---

## 🐛 Common Problems

### "No API Keys found!"

You forgot to add your key.

**Fix:**
```bash
# Make sure .env file exists
cp .env.template .env

# Edit it and add your key
nano .env  # or use any text editor
```

### "Tesseract not found"

Tesseract isn't installed.

**Windows fix:**
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Install it
- Add to `.env`: `TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe`

**Mac/Linux fix:**
```bash
# Mac
brew install tesseract

# Linux
sudo apt-get install tesseract-ocr
```

### "pdf2image failed"

Poppler isn't installed (needed for PDFs).

**Windows fix:**
- Download: https://github.com/oschwartz10612/poppler-windows/releases
- Extract it
- Add the `bin` folder to your PATH

**Linux fix:**
```bash
sudo apt-get install poppler-utils
```

### "Rate limit hit"

Sending requests too fast.

**Fix:**
- Add more API keys
- Wait between uploads
- Use batch processing (has delays built in)

### "Invalid JSON from AI"

AI gave back bad data.

**Fix:**
- Check your API key works and has credit
- Make sure file isn't corrupted
- Try again (might be temporary)
- Check if you hit token limits

**Turn on debug mode:**
```
DEBUG_MODE=true
```
Add this to your `.env` file to see more details.

---



