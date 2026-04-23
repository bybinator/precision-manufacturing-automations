# Automation Maintenance Guide

## Daily Checks

- Verify new invoices landed in Airtable (spot-check 1–2 records)
- If using the Drive watcher: confirm PDFs moved from "Invoices" to "Invoices/Processed"
- If anything looks off, check logs before EOD

---

## Weekly Tasks

**Check error logs:**
```bash
cat automations/invoice-processor/logs/processing_$(date +%Y-%m-%d).log | grep ERROR
```

**Verify web app is responsive:**
Open https://invoicewebapp-navy.vercel.app — confirm it loads in under 5 seconds.

**Review Airtable for "Needs Review" records:**
- Open Airtable → filter by Status = "Needs Review"
- Manually confirm or correct those records
- If same vendor keeps triggering "Needs Review", add them to `vendor_map.json`

---

## Monthly Tasks

**Update dependencies:**
```bash
# Invoice processor / Drive watcher
cd automations/invoice-processor
pip install --upgrade pdfplumber python-dotenv requests

cd ../drive-automation
pip install --upgrade google-auth-oauthlib google-api-python-client

# Web app backend
cd ../../invoice-upload-webapp/backend
pip install --upgrade -r requirements.txt
```

**Archive old logs:**
```bash
# Move logs older than 30 days to an archive folder
cd automations/invoice-processor/logs
mkdir -p archive
find . -name "*.log" -mtime +30 -exec mv {} archive/ \;
```

**Archive old processed invoices in Drive:**
Move files older than 60 days from "Invoices/Processed" into a dated archive subfolder (e.g., "Invoices/Archive/2026-04").

**Test end-to-end:**
Run a known good invoice through all three methods (local script, Drive watcher, web app) and confirm Airtable records are correct.

**Check Vercel deployment status:**
Go to https://vercel.com → invoicewebapp-navy → confirm the latest deployment is healthy.

---

## Quarterly Tasks

**Full system audit:**
- Confirm all three automations are functional
- Review Airtable base structure (column names match what scripts expect)
- Check Google Cloud Console — confirm Drive API is still enabled, no quota issues
- Review `vendor_map.json` — add any new image-logo vendors discovered

**Update documentation:**
If any processes changed, update the relevant runbook. Outdated docs are worse than no docs.

**Review automation effectiveness:**
Pull Airtable records for the quarter — how many invoices processed? Any patterns in "Needs Review" records? Any invoice formats still failing?

**Commit any accumulated changes:**
```bash
cd precision-manufacturing-automations
git add .
git commit -m "Quarterly maintenance update - $(date +%Y-Q%q)"
git push
```

---

## Annual Tasks

**Rotate API credentials:**
- Generate new Airtable API token
- Update `.env` files on all machines running local scripts
- Update Vercel environment variables for the web app (Vercel dashboard → Settings → Environment Variables)

**Major version review:**
- Check Python version: `python --version` — upgrade if on 3.8 (EOL)
- Review if pdfplumber has major updates that improve extraction

**Full ROI analysis:**
Calculate total invoices processed × time saved per invoice × labor cost. Present to Finance/management as proof of value.

---

## Emergency Procedures

**Automation broken, invoices need processing today:**
1. Use the manual fallback — Finance logs into Airtable and enters data directly
2. PDFs in Drive or local folder are not lost — they'll be processed once fixed
3. Fix the broken automation, then re-run on the backlog

**Airtable API is down:**
Check https://status.airtable.com. If confirmed down, wait it out — usually resolved within hours. Scripts will fail gracefully; PDFs are not lost.

**Google Drive API quota exceeded:**
Extremely unlikely (1 billion requests/day free tier). If it happens, wait 24 hours for reset. Check Console for quota usage.

**Vercel deployment broken:**
Roll back to previous deployment:
Vercel dashboard → Deployments → click any good previous deployment → "Promote to Production"

**Lost `.env` file or credentials:**
- Airtable token: regenerate at https://airtable.com/account
- Google credentials: re-download from Google Cloud Console → project "Invoice Drive Automation"
- Delete `token.json` and re-authenticate Google OAuth by running the Drive watcher manually

**Someone accidentally deleted Airtable records:**
Airtable has a trash/undo feature. Go to Airtable → base → search for recently deleted records. If beyond recovery, re-run the invoice processor on the original PDFs to regenerate the records.

---

## Maintenance Schedule Summary

| Frequency | Task |
|-----------|------|
| Daily | Spot-check Airtable records, verify Drive file movement |
| Weekly | Review error logs, check web app, review "Needs Review" records |
| Monthly | Update dependencies, archive logs, test end-to-end, check Vercel |
| Quarterly | Full audit, update docs, review vendor map, commit changes |
| Annually | Rotate credentials, major version check, ROI analysis |
