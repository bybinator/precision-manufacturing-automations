# Precision Manufacturing Invoice Automations

**Automated invoice processing system built with Python and Claude Code**

Three automations that eliminate manual invoice data entry for a manufacturing company's Finance department — saving 10+ hours per week.

**Live Demo:** https://invoicewebapp-navy.vercel.app
**GitHub (web app):** https://github.com/bybinator/invoice-webapp

---

## What This Solves

The Finance team was manually processing 20+ PDF invoices per day:
- Open PDF → read invoice number, vendor, date, amount → type into spreadsheet → copy to Airtable
- 10–15 hours per week of manual work
- Frequent typos and data entry errors

These three automations handle the entire workflow automatically.

---

## The Three Automations

### 1. Local Invoice Processor
**Location:** `automations/invoice-processor/`

Processes a folder of PDF invoices in one command. Extracts all key fields and sends them straight to Airtable.

```bash
python invoice_processor.py
```

- Extracts: invoice number, vendor, date, due date, amount
- Handles multiple invoice formats and layouts
- Confidence scoring — flags low-confidence records for manual review
- Vendor map for image-logo vendors (address-based lookup)

### 2. Google Drive Watcher
**Location:** `automations/drive-automation/`

Watches a Google Drive folder. Drop a PDF in — it gets processed automatically, no command needed.

```bash
python drive_invoice_watcher.py
```

- OAuth 2.0 authentication (saves token, no re-login needed)
- Downloads PDFs, processes them, sends to Airtable
- Works with real vendor invoices (tested with Trust Y produce supplier)

### 3. Invoice Upload Web App
**Location:** `automations/invoice-webapp/`

A web interface for the Finance team. Upload a PDF, review the extracted data, click Save.

- **Live:** https://invoicewebapp-navy.vercel.app
- Drag-and-drop PDF upload
- Editable fields before saving (in case extraction needs correction)
- Deployed on Vercel — works on any phone or computer

---

## Setup

### Requirements
- Python 3.8+
- Airtable account (free tier)
- Google Cloud account (for Drive automation only)

### Install dependencies
```bash
pip install pdfplumber python-dotenv requests flask flask-cors google-auth-oauthlib google-api-python-client
```

### Environment variables
Create a `.env` file:
```
AIRTABLE_TOKEN=your_token_here
AIRTABLE_BASE_ID=your_base_id_here
AIRTABLE_TABLE_NAME=Invoices
```

### Google Drive setup (automation #2 only)
- Create a Google Cloud project
- Enable Google Drive API
- Create OAuth credentials (Desktop App)
- Download as `credentials.json` and place in `automations/drive-automation/`

---

## Results

| Metric | Before | After |
|--------|--------|-------|
| Time per invoice | 3–5 min manual | ~2 sec automated |
| Daily processing time | 2+ hours | < 5 min review |
| Error rate | ~5% (human typos) | < 1% |
| Invoices accessible | Scattered in email | All in Airtable |

---

## Technical Stack

- **Python** — core extraction logic (pdfplumber, regex)
- **Airtable API** — database storage
- **Google Drive API** — cloud file watching
- **Flask** — web app backend
- **Vercel** — deployment
- **Claude Code** — AI-assisted development

---

## Key Design Decisions

**Why regex over AI for extraction?**
Fast, free, deterministic. For structured documents like invoices, regex patterns are more reliable than AI when the format is consistent.

**Why a confidence score?**
Not all PDFs extract cleanly (corrupted fonts, image logos, unusual layouts). The confidence score (0–1) flags records that need human review instead of silently failing.

**Why a vendor map?**
Some vendors use image logos — pdfplumber can't read images. The `vendor_map.json` file maps known street addresses to vendor names as a fallback.

---

## Built By

Andrew Bybee — AI Operations
- LinkedIn: [add yours]
- Built as part of the Claude Code for AI Operators course

---

*Built with Claude Code — AI-assisted development*
