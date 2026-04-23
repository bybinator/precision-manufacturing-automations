#!/usr/bin/env python3
"""
Invoice Upload Web App - Backend
Flask API that accepts PDF uploads, extracts invoice data, and saves to Airtable.
Built during Lesson 2.4 - Precision Manufacturing Co.
"""

import os
import sys
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Add parent directory so we can import from invoice-processor
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'invoice-processor'))
from invoice_processor import extract_text_from_pdf, extract_invoice_data, create_airtable_record

load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow browser requests from frontend

# Max upload size: 10MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024


@app.route('/api/health', methods=['GET'])
def health():
    """Simple health check so the frontend can confirm the server is running."""
    return jsonify({'status': 'ok'})


@app.route('/api/process', methods=['POST'])
def process_invoice():
    """
    Accept a PDF upload, extract invoice data, return it as JSON.
    The frontend shows this data to the user for review before saving.
    """
    # 1. Check a file was actually sent
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are supported'}), 400

    # 2. Save to a temp file (we need a path for pdfplumber)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    try:
        file.save(tmp.name)
        tmp.close()

        # 3. Extract text and invoice data (reuses Lesson 2.2 logic)
        text = extract_text_from_pdf(tmp.name)
        if not text:
            return jsonify({'error': 'Could not extract text from PDF. File may be a scanned image.'}), 422

        invoice_data = extract_invoice_data(text)
        invoice_data['source_file'] = file.filename

        # 4. Return extracted data for the user to review
        return jsonify({
            'success': True,
            'data': {
                'invoice_number': invoice_data.get('invoice_number'),
                'vendor_name':    invoice_data.get('vendor_name'),
                'invoice_date':   invoice_data.get('invoice_date'),
                'due_date':       invoice_data.get('due_date'),
                'total_amount':   invoice_data.get('total_amount'),
                'confidence':     invoice_data.get('confidence_score'),
                'source_file':    file.filename,
            }
        })

    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500
    finally:
        # Always clean up the temp file
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


@app.route('/api/save', methods=['POST'])
def save_invoice():
    """
    Accept reviewed invoice data as JSON and save it to Airtable.
    Called after the user has reviewed (and optionally edited) the extracted data.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Build the invoice_data dict that create_airtable_record expects
    invoice_data = {
        'invoice_number':   data.get('invoice_number'),
        'vendor_name':      data.get('vendor_name'),
        'invoice_date':     data.get('invoice_date'),
        'due_date':         data.get('due_date'),
        'total_amount':     data.get('total_amount'),
        'confidence_score': data.get('confidence', 1.0),
        'source_file':      data.get('source_file', 'Web Upload'),
    }

    success = create_airtable_record(invoice_data)

    if success:
        return jsonify({'success': True, 'message': 'Invoice saved to Airtable'})
    else:
        return jsonify({'error': 'Failed to save to Airtable. Check your credentials.'}), 500


if __name__ == '__main__':
    print("Starting Invoice Upload Server...")
    print("Open frontend/index.html in your browser to use the app.")
    app.run(debug=True, port=5000)
