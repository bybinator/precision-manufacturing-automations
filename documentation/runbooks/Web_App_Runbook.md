# Invoice Upload Web App — Runbook

## Overview

**What it does:** A web interface at https://invoicewebapp-navy.vercel.app where Finance staff can upload a PDF invoice, review the auto-extracted data, correct any fields if needed, and click Save to push the record to Airtable.

**Why it exists:** Not everyone can run Python scripts. The web app gives non-technical team members a clean, self-service way to process invoices from any browser on any device — no installation, no command line.

**Who uses it:** Finance team (primary). Anyone who needs to process a one-off invoice.

**Impact:** Same extraction quality as the local script, accessible to the entire team. Designed for the "I just got this invoice in my email" use case.

**Live URL:** https://invoicewebapp-navy.vercel.app

---

## Setup & Prerequisites

**For end users:** No setup needed. Just open the URL in a browser.

**For developers/maintainers:**
- Node.js (for Vercel CLI)
- Python 3.8+ (for local backend testing)
- Vercel account (free) — project is `invoicewebapp-navy`
- GitHub account with access to: https://github.com/bybinator/invoice-webapp

**Vercel environment variables (already configured):**
These are set in the Vercel dashboard — do not change unless credentials rotate:
- `AIRTABLE_TOKEN`
- `AIRTABLE_BASE_ID`
- `AIRTABLE_TABLE_NAME`

**To access Vercel dashboard:**
Log in at https://vercel.com → project: `invoicewebapp-navy`

---

## How to Use It (End User)

1. Go to https://invoicewebapp-navy.vercel.app
2. Click "Choose PDF" or drag-and-drop an invoice PDF onto the upload zone
3. Click "Process Invoice"
4. Review the extracted fields — edit any that look wrong
5. Click "Save to Airtable"
6. Done — record is in Airtable

The whole process takes about 30 seconds.

---

## How to Run Locally (Development/Testing)

**Start the backend:**
```bash
cd invoice-upload-webapp/backend
pip install -r requirements.txt
python app.py
```
Server starts at http://localhost:5000

**Open the frontend:**
Open `invoice-upload-webapp/frontend/index.html` directly in a browser.

The frontend is pre-configured to point at `localhost:5000` when running locally.

---

## How to Redeploy

If you make changes to the backend or frontend and need to push to production:

```bash
cd invoice-upload-webapp
git add .
git commit -m "describe your change"
git push
```

Vercel auto-deploys from the GitHub repo on every push to main. The live URL updates within ~2 minutes.

**To deploy manually via CLI:**
```bash
npm i -g vercel   # one-time install
vercel            # deploy
```

---

## What Could Go Wrong

**Page won't load / blank screen**
- Check https://vercel.com for outage status
- Try a hard refresh (Ctrl+Shift+R)
- Try a different browser

**"Process Invoice" button does nothing after upload**
- Make sure the file is a PDF (not a JPG or Word doc)
- File may be too large — try compressing the PDF
- Check browser console (F12 → Console) for errors

**Fields extract as empty or wrong**
This is an extraction issue, not an app issue. The PDF may have an unusual format. Use the editable fields to correct the data before saving. Report the invoice format so we can add support for it.

**"Save to Airtable" fails**
- Usually means Airtable credentials expired or the base was deleted
- Go to Vercel dashboard → Settings → Environment Variables
- Verify `AIRTABLE_TOKEN`, `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE_NAME` are all set correctly

**CORS error in browser console**
Only happens during local development. Make sure you're running the backend (`python app.py`) and opening the frontend file directly — don't serve the frontend from a different port.

**Vercel deployment failed after a push**
Go to https://vercel.com → project → Deployments → click the failed deployment → read the build log. Most common causes: missing package in `requirements.txt`, syntax error in Python code.

---

## Monitoring & Verification

**Check the app is live:**
Open https://invoicewebapp-navy.vercel.app — if it loads, it's up.

**Check Vercel logs:**
Vercel dashboard → project → Functions → view real-time logs for API calls and errors.

**Verify records are saving:**
After a test upload, check Airtable for the new row. Should appear within 5 seconds of clicking Save.

---

## Maintenance

**Monthly:**
- Open the app and do a test upload to confirm end-to-end flow
- Check Vercel dashboard for any deployment errors
- Verify Airtable credentials haven't been rotated

**To update dependencies:**
Edit `invoice-upload-webapp/backend/requirements.txt`, push to GitHub — Vercel redeploys automatically.

**Vercel free tier limits:**
- 100GB bandwidth/month
- 100 serverless function executions/day (per hobby plan)
- For higher volume, upgrade to Vercel Pro (~$20/month) or migrate to Render

---

## Emergency Procedures

**App is down and Finance needs to process invoices now:**
Fall back to the local invoice processor:
```bash
cd automations/invoice-processor
# put PDFs in invoices/ folder
python invoice_processor.py
```

**Need to roll back a bad deployment:**
Vercel dashboard → Deployments → click any previous deployment → "Promote to Production"

**Lost access to Vercel:**
The GitHub repo at https://github.com/bybinator/invoice-webapp has all the code. Re-deploy from scratch with `vercel --prod` from that repo directory.

**Airtable base was deleted:**
Create a new base with the same column names, update `AIRTABLE_BASE_ID` in Vercel environment variables, redeploy.
