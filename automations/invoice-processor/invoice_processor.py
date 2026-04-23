#!/usr/bin/env python3
"""
Invoice PDF Processor
Extracts invoice data from PDFs and uploads to Airtable
Built during Lesson 2.2 - Precision Manufacturing Co.
"""

import pdfplumber
import os
import sys
import re
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Airtable configuration
AIRTABLE_TOKEN = os.getenv('AIRTABLE_TOKEN')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME', 'Invoices')

# Set up logging - writes to both terminal and log file
_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(_LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(_LOG_DIR, f'processing_{datetime.now().strftime("%Y-%m-%d")}.log'), encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
# Fix Windows terminal Unicode issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
logger = logging.getLogger(__name__)


# Load vendor address→name mapping (for vendors whose names are image logos)
_VENDOR_MAP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vendor_map.json')
try:
    with open(_VENDOR_MAP_PATH, encoding='utf-8') as _f:
        VENDOR_MAP = json.load(_f)
except Exception:
    VENDOR_MAP = {}


# ─────────────────────────────────────────
# STEP 1: READ THE PDF
# ─────────────────────────────────────────

def strip_html(text: str) -> str:
    """Remove HTML tags and clean up leftover whitespace."""
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'[ \t]+', ' ', clean)
    return clean


def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """Extract all text from a PDF file, stripping HTML tags."""
    try:
        logger.info(f"Opening PDF: {os.path.basename(pdf_path)}")
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        text = strip_html(text)
        logger.info(f"Extracted {len(text)} characters from PDF")
        return text if text.strip() else None
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        return None


# ─────────────────────────────────────────
# STEP 2: EXTRACT FIELDS FROM TEXT
# ─────────────────────────────────────────

def extract_invoice_number(text: str) -> Optional[str]:
    """Extract invoice number - handles 'Invoice Number:', 'Invoice #:', etc."""
    patterns = [
        r'Invoice\s+Number\s*:\s*([A-Z]{2,}-\d{4}-\d+)',   # Invoice Number: INV-2024-0342
        r'Invoice\s*#\s*:\s*([A-Z]{2,}-\d{4}-\d+)',         # Invoice #: OD-2024-8823
        r'Invoice\s*#\s*:\s*([A-Z]{2,}-\d+)',               # Invoice #: WS-789456
        r'Invoice\s+Number\s*:\s*([A-Z0-9-]{4,20})',        # generic fallback
        r'Invoice\s*#\s*:\s*([A-Z0-9-]{4,20})',             # generic fallback
        r'Invoice\s+No\.?\s*:\s*([A-Z0-9-]+)',              # Invoice No: ...
        r'INVOICE\s*\n\s*(\d{4,8})\b',                              # Table: INVOICE\n221367
        r'INVOICE\s+DATE[^\n]{0,80}\n[^\n]{0,80}(\d{4,8})\s*$',  # Table row: last number after date
        r'(?:\d{1,2}[-/]\d{1,2}[-/]\d{4})\s+(\d{4,8})\b',        # Number right after MM-DD-YYYY date
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result = match.group(1).strip()
            # Reject if it captured a common word instead of an ID
            if result.lower() not in ('number', 'date', 'invoice', 'no'):
                logger.info(f"Invoice number: {result}")
                return result
    logger.warning("Could not find invoice number")
    return None


def extract_vendor_name(text: str) -> Optional[str]:
    """Extract vendor name — looks only in the letterhead section before SHIP TO / BILL TO."""

    # Only search the portion of the document before the customer address block
    cutoff = len(text)
    for marker in ['SHIP TO', 'BILL TO', 'Ship To', 'Bill To']:
        pos = text.find(marker)
        if 0 < pos < cutoff:
            cutoff = pos
    search_text = text[:cutoff]

    lines = [l.strip() for l in search_text.split('\n') if l.strip()]

    skip_keywords = ['factory road', 'industrial park', 'invoice', 'phone', 'fax',
                     'email', 'www', 'page ', 'continued', 'account', 'c. po no']

    suffixes = ['Corp', 'Inc', 'LLC', 'Ltd', 'Limited', 'Corporation',
                'Company', 'Co.', 'Supply', 'Supplies', 'Shipping', 'Direct',
                'Solutions', 'Trust', 'Foods', 'Produce', 'Wholesale', 'Distribution',
                'Manufacturing', 'Industries', 'Partners', 'Group', 'Services']

    for line in lines[:20]:
        # Strip non-ASCII (Korean, arrows, etc.) and remove QR code boilerplate
        clean = re.sub(r'[^\x00-\x7F]+', ' ', line)
        clean = re.sub(r'\bQR\s+CODE\s+SCAN\b', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s+', ' ', clean).strip()

        lower = clean.lower()
        if not clean or any(kw in lower for kw in skip_keywords):
            continue
        # Skip address lines (start with street number)
        if re.match(r'^\d+\s+[A-Z]', clean):
            continue
        # Skip phone/fax lines
        if re.match(r'^(TEL|FAX|PHONE|\(?\d{3}\)?)', clean, re.IGNORECASE):
            continue

        for suffix in suffixes:
            if re.search(r'\b' + re.escape(suffix) + r'\b', clean, re.IGNORECASE):
                words = clean.split()
                for i, word in enumerate(words):
                    if re.search(r'\b' + re.escape(suffix) + r'\b', word, re.IGNORECASE):
                        # Include one extra word if it's short (e.g. "Trust Y")
                        end = i + 1
                        if end < len(words) and len(words[end]) <= 4:
                            end += 1
                        vendor = ' '.join(words[:end]).strip()
                        if vendor and len(vendor) <= 60:
                            logger.info(f"Vendor: {vendor}")
                            return vendor
                        break

    # Fallback: first short clean line that isn't an address or phone
    for line in lines[:10]:
        clean = re.sub(r'[^\x00-\x7F]+', ' ', line)
        clean = re.sub(r'\bQR\s+CODE\s+SCAN\b', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s+', ' ', clean).strip()
        lower = clean.lower()
        if not clean or any(kw in lower for kw in skip_keywords):
            continue
        if re.match(r'^\d', clean):
            continue
        if re.match(r'^(TEL|FAX|PHONE)', clean, re.IGNORECASE):
            continue
        if 3 < len(clean) <= 60:
            logger.info(f"Vendor (fallback): {clean}")
            return clean

    # Last resort: look for a known vendor address in the text and map to name
    addr_pattern = r'(\d+\s+[A-Z][\w\s]+(?:Ave|Blvd|St|Rd|Dr|Way|Lane|Ln|Court|Ct|Place|Pl))'
    for addr_match in re.finditer(addr_pattern, search_text, re.IGNORECASE):
        addr = addr_match.group(1).strip()
        for key, name in VENDOR_MAP.items():
            if key.lower() in addr.lower():
                logger.info(f"Vendor (address lookup): {name}")
                return name

    logger.warning("Could not find vendor name")
    return None


def normalize_date(date_str: str) -> Optional[str]:
    """Convert various date formats to YYYY-MM-DD."""
    date_str = date_str.strip()
    formats = ['%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%Y/%m/%d', '%B %d, %Y', '%b %d, %Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return date_str


DATE_PATTERN = r'(\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})'

def extract_date(text: str, label: str = "Invoice Date") -> Optional[str]:
    """Extract a date field by its label."""
    pattern = rf'{label}\s*:\s*{DATE_PATTERN}'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        result = normalize_date(match.group(1))
        logger.info(f"{label}: {result}")
        return result

    # Fallback for invoice date: try plain "Date:" if "Invoice Date" not found
    if label == "Invoice Date":
        match = re.search(rf'(?<!\w)Date\s*:\s*{DATE_PATTERN}', text, re.IGNORECASE)
        if match:
            result = normalize_date(match.group(1))
            logger.info(f"{label} (via 'Date:'): {result}")
            return result
        # Table format: "INVOICE DATE" with date on same line or next line (no colon)
        match = re.search(rf'INVOICE\s+DATE[^\n]{{0,100}}({DATE_PATTERN})', text, re.IGNORECASE)
        if not match:
            match = re.search(rf'INVOICE\s+DATE[^\n]*\n[^\n]{{0,100}}({DATE_PATTERN})', text, re.IGNORECASE)
        if match:
            result = normalize_date(match.group(1))
            logger.info(f"{label} (via table header): {result}")
            return result

    logger.warning(f"Could not find {label}")
    return None


def extract_amount(text: str) -> Optional[float]:
    """
    Extract the final total amount due.
    Tries 'Total Due', 'Amount Due', 'Total Amount' before plain 'Total'.
    Avoids matching 'Subtotal'.
    """
    priority_patterns = [
        r'Total\s+Due\s*:?\s*>?\s*\$?\s*([\d,]+\.\d{2})',
        r'Amount\s+Due\s*:?\s*>?\s*\$?\s*([\d,]+\.\d{2})',
        r'Total\s+Amount\s*:?\s*>?\s*\$?\s*([\d,]+\.\d{2})',
    ]
    for pattern in priority_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = float(match.group(1).replace(',', ''))
            logger.info(f"Total (priority match): ${amount:.2f}")
            return amount

    # Fallback: plain "Total" but NOT "Subtotal"
    for match in re.finditer(r'(?<!Sub)Total\s*:?\s*\$?\s*([\d,]+\.\d{2})', text, re.IGNORECASE):
        amount = float(match.group(1).replace(',', ''))
        logger.info(f"Total (fallback): ${amount:.2f}")
        return amount

    logger.warning("Could not find total amount")
    return None


def extract_invoice_data(text: str) -> Dict:
    """Extract all fields and calculate confidence score."""
    data = {
        'invoice_number': extract_invoice_number(text),
        'vendor_name':    extract_vendor_name(text),
        'invoice_date':   extract_date(text, 'Invoice Date'),
        'due_date':       extract_date(text, 'Due Date'),
        'total_amount':   extract_amount(text),
        'extracted_at':   datetime.now().isoformat(),
    }

    # Confidence: each of 5 key fields found = 0.20 points
    key_fields = ['invoice_number', 'vendor_name', 'invoice_date', 'due_date', 'total_amount']
    found = sum(1 for f in key_fields if data.get(f) is not None)
    data['confidence_score'] = round(found / len(key_fields), 2)

    logger.info(f"Confidence score: {data['confidence_score']} ({found}/5 fields found)")
    return data


# ─────────────────────────────────────────
# STEP 3: SEND TO AIRTABLE
# ─────────────────────────────────────────

def create_airtable_record(invoice_data: Dict) -> bool:
    """Create a record in Airtable with extracted invoice data."""
    if not AIRTABLE_TOKEN or not AIRTABLE_BASE_ID:
        logger.error("Airtable credentials missing — check your .env file")
        return False

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    }

    # Determine status based on confidence
    if invoice_data['confidence_score'] >= 0.8:
        status = "received"
    else:
        status = "Needs Review"

    fields = {
        "Invoice Number": invoice_data.get('invoice_number'),
        "Vendor":         invoice_data.get('vendor_name'),
        "Invoice Date":   invoice_data.get('invoice_date'),
        "Amount":         invoice_data.get('total_amount'),
        "Status":         status,
        "Source File":    invoice_data.get('source_file', ''),
    }

    # Remove None values — Airtable rejects null fields
    fields = {k: v for k, v in fields.items() if v is not None}

    try:
        response = requests.post(url, headers=headers, json={"fields": fields})
        if response.status_code in (200, 201):
            record_id = response.json().get('id')
            logger.info(f"✓ Airtable record created: {record_id}")
            return True
        else:
            logger.error(f"✗ Airtable error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"✗ Exception sending to Airtable: {e}")
        return False


# ─────────────────────────────────────────
# STEP 4: PROCESS ONE FILE
# ─────────────────────────────────────────

def process_invoice_file(pdf_path: str) -> Dict:
    """Full pipeline for one PDF: read → extract → send to Airtable."""
    filename = os.path.basename(pdf_path)
    logger.info(f"\n{'='*50}")
    logger.info(f"Processing: {filename}")
    logger.info(f"{'='*50}")

    result = {'filename': filename, 'success': False, 'errors': []}

    # Read PDF
    text = extract_text_from_pdf(pdf_path)
    if not text:
        result['errors'].append("Could not extract text from PDF")
        return result

    # Extract data
    invoice_data = extract_invoice_data(text)
    invoice_data['source_file'] = filename
    result['data'] = invoice_data

    # Warn if low confidence but still try to save
    if invoice_data['confidence_score'] < 0.6:
        result['errors'].append(f"Very low confidence ({invoice_data['confidence_score']}) — needs manual review")
        logger.warning("Low confidence — will save with 'Needs Review' status")

    # Send to Airtable
    if create_airtable_record(invoice_data):
        result['success'] = True
    else:
        result['errors'].append("Failed to create Airtable record")

    return result


# ─────────────────────────────────────────
# STEP 5: PROCESS ALL INVOICES
# ─────────────────────────────────────────

def main():
    logger.info("=== Invoice Processor Starting ===")

    # Path to sample invoices (relative to this script)
    invoice_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "precision-manufacturing", "current-data-samples", "invoices"
    )

    if not os.path.exists(invoice_dir):
        logger.error(f"Invoice directory not found: {invoice_dir}")
        return

    # Get all PDFs
    pdf_files = sorted([
        os.path.join(invoice_dir, f)
        for f in os.listdir(invoice_dir)
        if f.endswith('.pdf')
    ])

    if not pdf_files:
        logger.error("No PDF files found")
        return

    logger.info(f"Found {len(pdf_files)} invoices to process")

    # Process each one
    results = []
    for pdf_path in pdf_files:
        result = process_invoice_file(pdf_path)
        results.append(result)

    # Print summary
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful

    print("\n" + "="*50)
    print("PROCESSING SUMMARY")
    print("="*50)
    print(f"Total:      {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")
    print()

    for r in results:
        icon = "✓" if r['success'] else "✗"
        print(f"{icon} {r['filename']}")
        if r.get('data'):
            d = r['data']
            print(f"    Vendor:    {d.get('vendor_name', 'NOT FOUND')}")
            print(f"    Invoice #: {d.get('invoice_number', 'NOT FOUND')}")
            print(f"    Amount:    {d.get('total_amount', 'NOT FOUND')}")
            print(f"    Confidence:{d.get('confidence_score', 0)}")
        for err in r.get('errors', []):
            print(f"    ⚠ {err}")

    print("="*50)
    print(f"\nCheck your Airtable base to see the records!")
    logger.info("=== Processing Complete ===")


if __name__ == "__main__":
    main()
