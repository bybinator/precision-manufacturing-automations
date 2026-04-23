# Invoice Automations — Frequently Asked Questions

---

## General Questions

**Q: Who built these automations?**
Andrew Bybee, AI Operations. Built April 2026 as part of the Precision Manufacturing automation initiative.

**Q: What problem do they solve?**
Finance was manually processing 20+ PDF invoices per day — opening each one, reading the data, typing it into Airtable. That's 2–3 hours of daily work with a ~5% error rate. These automations do it automatically in under a minute.

**Q: Are they reliable?**
Yes. Tested with real vendor invoices including multi-page PDFs and image-logo vendors. Confidence scoring flags any records that need human review so nothing slips through silently.

**Q: What if they break?**
Each automation has a fallback — the manual process still works. See each runbook's Emergency Procedures section. Contact Andrew Bybee for fixes.

**Q: Can we modify them?**
Yes. All code is in GitHub at https://github.com/bybinator/precision-manufacturing-automations. Changes should be tested locally before pushing to production.

**Q: Do these cost anything to run?**
No. All services used are on free tiers: Airtable (free), Google Drive API (free), Vercel (free hobby tier). If invoice volume grows significantly (100+ per day), Vercel's free tier may need upgrading (~$20/month).

---

## Technical Questions

**Q: What APIs do these automations use?**
- Airtable API — database storage
- Google Drive API — file watching and download
- Vercel — web app hosting (serverless)

**Q: Where are credentials stored?**
In `.env` files on the machine running the scripts. Never in the code. Never in GitHub. The `.gitignore` file prevents them from being committed accidentally.

**Q: How do we update the vendor list for image-logo vendors?**
Edit `automations/invoice-processor/vendor_map.json`. Add a line with the vendor's street address and their name:
```json
{"1234 Main St": "Vendor Name"}
```
This is needed for vendors whose logos are images (pdfplumber can't read images, so we use address as a fallback).

**Q: What Python version is required?**
Python 3.8 or higher.

**Q: How do we update dependencies?**
```bash
pip install --upgrade -r requirements.txt
```
Test after upgrading. If something breaks, downgrade the specific package to the version in `requirements.txt`.

**Q: What's the backup plan if an automation fails?**
Manual entry directly into Airtable. This was the original process and still works. See Emergency Procedures in each runbook.

**Q: Where are the logs?**
Local invoice processor: `automations/invoice-processor/logs/processing_YYYY-MM-DD.log`
Drive watcher: console output (pipe to file if you need persistence)
Web app: Vercel dashboard → Functions logs

---

## User Questions

**Q: How long does the invoice upload take?**
About 5–10 seconds to extract, then instant save. Total under 30 seconds.

**Q: What file formats are supported?**
PDF only. Invoices must be actual PDF files — not photos of invoices, not scanned images saved as PDF (those are just image files inside a PDF wrapper and won't extract properly).

**Q: What if my upload fails?**
Try again. If it keeps failing, check the file is a real PDF and under 10MB. If the problem persists, fall back to manual Airtable entry and contact IT.

**Q: Can I process multiple files at once?**
Not through the web app — one at a time. For bulk processing, use the local invoice processor script which handles a whole folder at once.

**Q: What does "Needs Review" mean in Airtable?**
The confidence score was below 80% — usually because a field is missing from the invoice (like no Due Date). The extracted data is likely correct, just spot-check it and update manually if needed.

**Q: What if I saved the wrong data?**
Go to Airtable and edit the record directly. The automation doesn't lock records.

---

## Business Questions

**Q: How much time do these automations save?**
- Invoice processor (local): ~15 hours/month
- Drive automation: ~5 additional hours/month (eliminates file management)
- Web app: makes processing accessible to the whole team, not just whoever runs the script

**Q: What's the ROI?**
At $35/hour admin labor: ~20 hours/month saved = $700/month = **$8,400/year**. One-time build cost: ~40 hours.

**Q: What would happen if we turned them off?**
Finance goes back to manually opening PDFs and typing data. ~2–3 hours per day of data entry work resumes, plus higher error rate (~5% vs current <1%).

**Q: Can this be expanded to other document types?**
Yes. The extraction logic works on any structured PDF. Packing slips, purchase orders, expense reports — same pattern, different regex. Each new document type takes a few hours to add support for.

**Q: Can we add more vendors to the system?**
Yes — and it's easy. For text-based vendor names, no change needed. For image-logo vendors, add one line to `vendor_map.json` with their street address.
