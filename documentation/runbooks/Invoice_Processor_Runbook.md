# Invoice Processing Automation — Runbook

## Overview

**What it does:** Scans a local folder of PDF invoices, extracts key fields (invoice number, vendor, date, due date, amount), and sends each record to Airtable automatically.

**Why it exists:** Finance was manually opening 20+ PDFs per day and typing data into spreadsheets — roughly 2–3 hours of daily data entry with a ~5% error rate. This script eliminates that entirely.

**Who uses it:** Finance team, or whoever is assigned to run end-of-day invoice processing.

**Impact:** Processes a full folder of invoices in under 30 seconds. Saves approximately 15+ hours per month.

---

## Setup & Prerequisites

**Software required:**
- Python 3.8+
- pip packages: `pdfplumber`, `python-dotenv`, `requests`

**Install dependencies:**
```bash
cd automations/invoice-processor
pip install pdfplumber python-dotenv requests
```

**Credentials required:**
- Airtable API token
- Airtable Base ID
- Airtable table name

**Where credentials live:**
Create a `.env` file in `automations/invoice-processor/`:
```
AIRTABLE_TOKEN=your_token_here
AIRTABLE_BASE_ID=your_base_id_here
AIRTABLE_TABLE_NAME=Invoices
```

Never commit `.env` to GitHub — it's in `.gitignore`.

**One-time setup:**
- Get Airtable token from: https://airtable.com/account → API section
- Get Base ID from your Airtable base URL: `https://airtable.com/appXXXXXXXX/...` — the `appXXXXXXXX` part is the Base ID
- Airtable table must have columns: Invoice Number, Vendor, Invoice Date, Due Date, Amount, Status, Confidence Score

---

## How to Run It

**Step 1 — Place PDFs in the invoices folder:**
```
automations/invoice-processor/invoices/
```

**Step 2 — Run the script:**
```bash
cd automations/invoice-processor
python invoice_processor.py
```

**What to expect:**
- Script prints one line per invoice processed
- Each successful record is sent to Airtable
- Any record below 80% confidence is flagged as "Needs Review" in Airtable (not an error — just needs a human check)
- Script finishes in under 1 minute for 20+ invoices

**What success looks like:**
- Terminal shows no ERROR lines
- New rows appear in Airtable within seconds of the script finishing
- Log file created at `automations/invoice-processor/logs/processing_YYYY-MM-DD.log`

---

## What Could Go Wrong

**Error: `ModuleNotFoundError: No module named 'pdfplumber'`**
Run: `pip install pdfplumber python-dotenv requests`

**Error: `KeyError: AIRTABLE_TOKEN`**
The `.env` file is missing or in the wrong folder. Check that `.env` exists in `automations/invoice-processor/`.

**Error: `401 Unauthorized` from Airtable**
Token is wrong or expired. Re-copy the token from Airtable account settings. Make sure the token has access to the correct base.

**Error: `FileNotFoundError: invoices/`**
The `invoices/` folder doesn't exist. Create it: `mkdir automations/invoice-processor/invoices`

**Vendor shows as `None` in Airtable**
The vendor logo is an image (not text) — pdfplumber can't read it. Add the vendor's street address to `vendor_map.json`:
```json
{"1234 Vendor Street": "Vendor Name"}
```

**Record flagged "Needs Review" but data looks correct**
This means confidence score is between 0.7–0.8. Usually happens when a field like Due Date is missing from the invoice format. Review the record in Airtable and manually confirm or correct.

**PDF processed but no Airtable record created**
Check the log file for that date. Look for lines containing `ERROR` or `FAILED`.

---

## Monitoring & Verification

**Check it ran:**
Open the log file at:
```
automations/invoice-processor/logs/processing_YYYY-MM-DD.log
```
Look for `SUCCESS` entries per invoice. Any `ERROR` lines indicate failures.

**Verify in Airtable:**
- New rows should appear with today's date
- Status column should show "Processed" (or "Needs Review" for low-confidence)
- Spot-check 2–3 records against the original PDFs

**Quick sanity check command:**
```bash
python invoice_processor.py 2>&1 | grep -E "ERROR|SUCCESS|processed"
```

---

## Maintenance

**Monthly:**
- Update packages: `pip install --upgrade pdfplumber python-dotenv requests`
- Archive logs older than 30 days from the `logs/` folder
- Test with one known invoice to confirm extraction still works

**As needed:**
- Add new vendors with image logos to `vendor_map.json`
- If a new invoice format fails to extract correctly, review the raw text by adding `print(text)` temporarily to `extract_text()` and adjust regex patterns

**Credentials:**
- Airtable tokens don't expire unless manually revoked
- If the token is rotated, update `.env` on every machine running this script

---

## Emergency Procedures

**Script completely broken and invoices need to go into Airtable today:**
1. Open each PDF manually
2. Log into Airtable directly at https://airtable.com
3. Manually enter the fields — this is the old process, it works as a fallback
4. Flag for investigation and fix the script tomorrow

**Airtable API is down:**
The script will fail with a connection error. Invoices won't be lost — PDFs are still in the `invoices/` folder. Re-run the script once Airtable is back up.

**To check Airtable status:** https://status.airtable.com

**Contact for help:** Andrew Bybee (built this automation) — see GitHub repo for contact info.
