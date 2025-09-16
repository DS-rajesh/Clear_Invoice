import pdfkit
import os

# Test if pdfkit is properly installed
try:
    # Simple HTML content for testing
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test PDF</title>
    </head>
    <body>
        <h1>PDFKit Test</h1>
        <p>This is a test PDF generated using pdfkit.</p>
    </body>
    </html>
    """
    
    # Configure pdfkit options
    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'no-outline': None
    }
    
    # Generate PDF
    pdf_data = pdfkit.from_string(html_content, False, options=options)
    print("PDFKit is working correctly!")
    print(f"Generated PDF size: {len(pdf_data)} bytes")
    
    # Save to file for verification
    with open('test_pdfkit_output.pdf', 'wb') as f:
        f.write(pdf_data)
    print("PDF saved to test_pdfkit_output.pdf")
    
except ImportError:
    print("pdfkit is not installed or not properly configured")
    print("Please install it with: pip install pdfkit")
    print("Also make sure wkhtmltopdf is installed on your system")
    
except Exception as e:
    print(f"Error generating PDF: {e}")