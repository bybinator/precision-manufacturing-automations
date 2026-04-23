# Google Drive Invoice Automation — Runbook

## Overview

**What it does:** Watches a Google Drive folder called "Invoices." When a PDF is dropped in, it automatically downloads it, extracts invoice data, sends it to Airtable, and moves the file to a "Processed" subfolder.

**Why it exists:** Eliminates the need to manually copy files to a local machine for processing. Finance team can drop invoices directly into Drive from any device — laptop, phone, anywhere — and the data appears in Airtable automatically.

**Who uses it:** Runs as a background process on a dedicated machine (or can be run manually). Finance staff just need to drop PDFs into the Drive folder.

**Impact:** Zero-touch invoice processing. Drop a file, it's in Airtable in under 60 seconds.

---

## Setup & Prerequisites

**Software required:**
- Python 3.8+
- pip packages: `google-auth-oauthlib`, `google-api-python-client`, `pdfplumber`, `python-dotenv`, `requests`

**Install dependencies:**
```bash
cd automations/drive-automation
pip install google-auth-oauthlib google-api-python-client pdfplumber python-dotenv requests
```

**Credentials required:**
- Google OAuth credentials (`credentials.json`) — Desktop App type
- Airtable API token, Base ID, table name (same as invoice processor)

**Where credentials live:**
- `automations/drive-automation/credentials.json` — Google OAuth (never commit to GitHub)
- `automations/drive-automation/.env` — Airtable credentials (same format as invoice processor)
- `automations/drive-automation/token.json` — auto-generated after first login, saves auth so you don't re-login

**One-time Google setup (already done — documenting for new maintainers):**
1. Go to Google Cloud Console → APIs & Services → Credentials
2. Project name: "Invoice Drive Automation"
3. Download OAuth credentials as `credentials.json` (Desktop App type)
4. Enable Google Drive API for the project
5. Add your Gmail as a Test User in OAuth consent screen (OAuth → Test Users)
6. First run will open a browser for login — after that, `token.json` handles auth automatically

---

## How to Run It

**Run manually (one-time check):**
```bash
cd automations/drive-automation
python drive_invoice_watcher.py
```

**Run continuously (background process):**
```bash
cd automations/drive-automation
python drive_invoice_watcher.py &
```
Or use a process manager like `pm2` or Windows Task Scheduler for production.

**What to expect:**
- Script starts and prints "Watching Drive folder: Invoices"
- When a PDF is detected, it prints the filename and extraction results
- Processed files are moved to an "Invoices/Processed" subfolder in Drive
- Data appears in Airtable within 60 seconds of the file being dropped

**What success looks like:**
- No ERROR lines in output
- New Airtable record with correct fields
- PDF moved out of "Invoices" folder into "Invoices/Processed"

---

## What Could Go Wrong

**Error: `FileNotFoundError: credentials.json`**
The Google credentials file is missing. Get it from Google Cloud Console → APIs & Services → Credentials → download the OAuth client JSON. Rename to `credentials.json` (watch for double extensions on Windows: `credentials.json.json`).

**Error: `403 access_denied` during OAuth login**
Your Gmail isn't added as a test user. Go to Google Cloud Console → OAuth consent screen → Test Users → add your Gmail.

**Error: `Token has been expired or revoked`**
Delete `token.json` and re-run. A browser will open for re-authentication. This only happens if you revoke access or the token gets corrupted.

**Script runs but finds no files**
The Drive folder might be named differently. The script looks for a folder named exactly "Invoices" (capital I). Check Drive and rename if needed.

**PDF downloaded but extraction fails**
The invoice format may be new/unsupported. The PDF will still be moved to "Processed" but the Airtable record may be incomplete. Check logs and add new patterns to `invoice_processor.py` if needed.

**`401 Unauthorized` from Airtable**
Same as invoice processor — check `.env` credentials.

---

## Monitoring & Verification

**Check it's running:**
```bash
ps aux | grep drive_invoice_watcher
```
(On Windows: check Task Manager for python processes)

**Check recent activity:**
Look in Google Drive → "Invoices/Processed" folder — files there have been handled.

**Verify in Airtable:**
New records should match files in the Processed folder, one-to-one.

**If you suspect it missed a file:**
Move the PDF back from "Processed" to "Invoices" — the watcher will pick it up again on the next poll.

---

## Maintenance

**Monthly:**
- Update packages: `pip install --upgrade google-auth-oauthlib google-api-python-client`
- Clear old files from "Invoices/Processed" in Drive (archive or delete after 90 days)
- Test with a known invoice to confirm end-to-end flow works

**Token refresh:**
`token.json` refreshes automatically. If it ever stops working, delete it and re-authenticate by running the script manually.

**Google Cloud project:**
- Project: "Invoice Drive Automation"
- Console: https://console.cloud.google.com
- No cost — Drive API is free for this usage level

---

## Emergency Procedures

**Watcher is down and invoices are piling up in Drive:**
1. Download the PDFs from Drive manually
2. Place them in `automations/invoice-processor/invoices/`
3. Run `python invoice_processor.py` to process them directly
4. Fix the watcher and re-deploy

**Google Drive API quota exceeded (rare):**
Free tier allows 1 billion requests/day — extremely unlikely to hit this. If it happens, wait 24 hours and it resets.

**Lost `credentials.json`:**
Re-download from Google Cloud Console. Project is "Invoice Drive Automation" under your Google account.

**To pause the automation:**
Kill the process:
```bash
pkill -f drive_invoice_watcher.py
```
Or stop the Task Scheduler job on Windows.
