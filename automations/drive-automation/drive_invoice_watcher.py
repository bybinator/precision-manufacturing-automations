#!/usr/bin/env python3
"""
Google Drive Invoice Watcher
Watches a Google Drive folder for new PDF invoices and processes them automatically.
Built during Lesson 2.3 - Precision Manufacturing Co.
"""

import os
import sys
import logging
import tempfile
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# Import our existing invoice processor functions
from invoice_processor import extract_text_from_pdf, extract_invoice_data, create_airtable_record

# Google Drive API scope — read-only is enough to download files
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# File to store your login token so you don't re-authenticate every run
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token.json')
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         f'logs/drive_{datetime.now().strftime("%Y-%m-%d")}.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler(sys.stdout)
    ]
)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
logger = logging.getLogger(__name__)


def authenticate():
    """Authenticate with Google Drive. Opens browser on first run, uses saved token after."""
    creds = None

    # Load saved token if it exists
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        logger.info("Authentication successful — token saved")

    return creds


def get_drive_service():
    """Build and return the Google Drive API service."""
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    return service


def find_invoices_folder(service, folder_name="Invoices"):
    """Find a folder in Google Drive by name. Returns folder ID or None."""
    results = service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()

    folders = results.get('files', [])
    if not folders:
        logger.warning(f"No folder named '{folder_name}' found in Google Drive")
        return None

    folder_id = folders[0]['id']
    logger.info(f"Found folder '{folder_name}' — ID: {folder_id}")
    return folder_id


def list_pdf_files(service, folder_id):
    """List all PDF files in a Drive folder."""
    results = service.files().list(
        q=f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false",
        fields="files(id, name, createdTime)",
        orderBy="createdTime desc"
    ).execute()

    files = results.get('files', [])
    logger.info(f"Found {len(files)} PDF(s) in Drive folder")
    return files


def download_pdf(service, file_id, file_name):
    """Download a PDF from Drive to a temp file. Returns the temp file path."""
    request = service.files().get_media(fileId=file_id)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix=file_name + '_')

    downloader = MediaIoBaseDownload(tmp, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    tmp.close()
    logger.info(f"Downloaded '{file_name}' to temp file")
    return tmp.name


def process_drive_invoices(folder_name="Invoices"):
    """Main function: find Drive folder, download PDFs, process each one."""
    logger.info("=== Drive Invoice Watcher Starting ===")

    service = get_drive_service()

    # Find the Invoices folder
    folder_id = find_invoices_folder(service, folder_name)
    if not folder_id:
        logger.error(f"Create a folder called '{folder_name}' in your Google Drive and upload PDFs to it.")
        return

    # List PDFs in the folder
    pdf_files = list_pdf_files(service, folder_id)
    if not pdf_files:
        logger.info("No PDFs found in the Drive folder. Upload some invoices and try again.")
        return

    results = []
    for drive_file in pdf_files:
        file_name = drive_file['name']
        file_id = drive_file['id']

        logger.info(f"\n{'='*50}")
        logger.info(f"Processing from Drive: {file_name}")
        logger.info(f"{'='*50}")

        result = {'filename': file_name, 'success': False, 'errors': []}

        # Download to temp file
        tmp_path = None
        try:
            tmp_path = download_pdf(service, file_id, file_name)

            # Extract text and data
            text = extract_text_from_pdf(tmp_path)
            if not text:
                result['errors'].append("Could not extract text from PDF")
                results.append(result)
                continue

            invoice_data = extract_invoice_data(text)
            invoice_data['source_file'] = f"Drive: {file_name}"
            result['data'] = invoice_data

            if invoice_data['confidence_score'] < 0.6:
                result['errors'].append(f"Low confidence ({invoice_data['confidence_score']}) — needs review")
                logger.warning("Low confidence — saving with 'Needs Review' status")

            # Send to Airtable
            if create_airtable_record(invoice_data):
                result['success'] = True
            else:
                result['errors'].append("Failed to create Airtable record")

        except Exception as e:
            result['errors'].append(f"Error: {e}")
            logger.error(f"Error processing {file_name}: {e}")
        finally:
            # Clean up temp file
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        results.append(result)

    # Print summary
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful

    print("\n" + "="*50)
    print("DRIVE PROCESSING SUMMARY")
    print("="*50)
    print(f"Total:      {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")
    print()

    for r in results:
        icon = "+" if r['success'] else "x"
        print(f"[{icon}] {r['filename']}")
        if r.get('data'):
            d = r['data']
            print(f"    Vendor:     {d.get('vendor_name', 'NOT FOUND')}")
            print(f"    Invoice #:  {d.get('invoice_number', 'NOT FOUND')}")
            print(f"    Amount:     {d.get('total_amount', 'NOT FOUND')}")
            print(f"    Confidence: {d.get('confidence_score', 0)}")
        for err in r.get('errors', []):
            print(f"    ! {err}")

    print("="*50)
    print("\nCheck your Airtable base to see the new records!")
    logger.info("=== Drive Processing Complete ===")


if __name__ == "__main__":
    process_drive_invoices()
