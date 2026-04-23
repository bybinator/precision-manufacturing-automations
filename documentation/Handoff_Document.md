# Precision Manufacturing Automations — Handoff Document

**Prepared by:** Andrew Bybee, AI Operations
**Date:** April 2026
**For:** Incoming maintainer / successor

---

## What You're Receiving

Three working automations that handle invoice processing for the Finance department:

| Automation | What it does | Status |
|-----------|-------------|--------|
| Local Invoice Processor | Batch-process a folder of PDFs → Airtable | Operational |
| Google Drive Watcher | Auto-process invoices dropped in Drive | Operational |
| Invoice Upload Web App | Self-service web tool for Finance staff | Operational (live at https://invoicewebapp-navy.vercel.app) |

**GitHub repository (all code):** https://github.com/bybinator/precision-manufacturing-automations
**Web app repo:** https://github.com/bybinator/invoice-webapp

---

## Quick Start for New Maintainer

1. **Get repository access** — request collaborator access to both GitHub repos above
2. **Clone the portfolio repo:**
   ```bash
   git clone https://github.com/bybinator/precision-manufacturing-automations
   ```
3. **Set up credentials** — you'll need:
   - Airtable API token (get from Finance lead or Airtable account)
   - Google OAuth credentials (get `credentials.json` from the Google Cloud project "Invoice Drive Automation")
   - Vercel access (request access to the `invoicewebapp-navy` project)
4. **Test each automation** — run a known invoice through each one and verify Airtable records
5. **Read the runbooks** — they're in `documentation/runbooks/`

---

## Key Contacts

| Role | Contact |
|------|---------|
| Previous maintainer (you) | Andrew Bybee |
| Finance lead (primary user) | [Finance department contact] |
| IT / Airtable admin | [IT contact] |
| Google Cloud account owner | andrewbybee0@gmail.com |

---

## Access You'll Need

- [ ] GitHub repos: https://github.com/bybinator/precision-manufacturing-automations and https://github.com/bybinator/invoice-webapp
- [ ] Airtable base access (Finance → Invoices base)
- [ ] Vercel project access (invoicewebapp-navy)
- [ ] Google Cloud Console access OR a copy of `credentials.json` from the "Invoice Drive Automation" project
- [ ] `.env` file with Airtable credentials for local scripts

---

## First Week Checklist

- [ ] Access to both GitHub repositories
- [ ] `.env` file configured and tested locally
- [ ] Successfully ran `invoice_processor.py` with at least one invoice
- [ ] Confirmed Drive watcher detects and processes a test PDF
- [ ] Confirmed web app at https://invoicewebapp-navy.vercel.app is functional
- [ ] Reviewed all three runbooks in `documentation/runbooks/`
- [ ] Met with Finance lead — understand their workflow and expectations
- [ ] Know what "Needs Review" means and what to do about those records
- [ ] Know how to add a new vendor to `vendor_map.json`

---

## First Month Goals

- [ ] Run each automation independently without help
- [ ] Troubleshoot at least one minor issue on your own
- [ ] Update `vendor_map.json` for any new image-logo vendors encountered
- [ ] Complete first monthly maintenance pass (see Maintenance Guide)
- [ ] Update documentation for anything you discover that's undocumented

---

## Known Issues & Workarounds

| Issue | Workaround |
|-------|-----------|
| Image-logo vendors extract as None | Add street address → vendor name to `vendor_map.json` |
| Trust Y invoices have no Due Date | Expected — confidence score will be ~80%, flagged "Needs Review" is normal |
| Some PDFs with corrupted font encodings fail entirely | Flag for manual entry; no automated fix currently |
| Vercel free tier: 100 function calls/day | Fine for current volume; upgrade if Finance grows significantly |

---

## Architecture Overview

```
PDF Invoice
    │
    ├── Local folder → invoice_processor.py → Airtable
    │
    ├── Google Drive folder → drive_invoice_watcher.py → invoice_processor.py → Airtable
    │
    └── Browser upload → Vercel (Flask backend) → invoice_processor.py → Airtable
```

All three automations share the same extraction logic (`invoice_processor.py`). Changes to extraction logic affect all three.

---

## Future Enhancement Ideas

- **Email-triggered processing:** Watch a Finance inbox for invoice attachments, auto-process them
- **Due date alerts:** Airtable automation to flag invoices due within 7 days
- **Timesheet automation:** Same pattern applied to employee hour tracking (strong candidate for next project)
- **Multi-format support:** Extend regex patterns to handle more vendor invoice formats
- **Bulk web upload:** Allow multiple PDFs to be uploaded at once in the web app

---

## Resources

| Resource | Link |
|----------|------|
| Portfolio repo (all code) | https://github.com/bybinator/precision-manufacturing-automations |
| Web app repo | https://github.com/bybinator/invoice-webapp |
| Live web app | https://invoicewebapp-navy.vercel.app |
| Airtable | https://airtable.com |
| Vercel dashboard | https://vercel.com |
| Google Cloud Console | https://console.cloud.google.com (project: Invoice Drive Automation) |
| Runbooks | `documentation/runbooks/` |
| Quick Start Guide | `documentation/quick-starts/Invoice_Web_App_Quick_Start.md` |
| FAQ | `documentation/training/FAQ.md` |
| Maintenance Guide | `documentation/training/Maintenance_Guide.md` |

---

## 30-Day Support

I'm available for questions during the first 30 days of your transition. Reach out before escalating to rebuilding anything — most issues have quick fixes documented in the runbooks.
