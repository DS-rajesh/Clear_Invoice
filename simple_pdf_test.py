#!/usr/bin/env python
"""
Simple test script to verify ReportLab PDF generation works correctly
without Django dependencies.
"""

import sys
import os

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
    import io
    print("✅ ReportLab imported successfully")
except ImportError as e:
    print(f"❌ Failed to import ReportLab: {e}")
    sys.exit(1)

def test_reportlab_pdf():
    """Test basic ReportLab PDF generation"""
    print("Creating test PDF...")
    
    # Create a BytesIO buffer to hold PDF data
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Add some content
    elements.append(Paragraph("Test PDF Generation", styles['Heading1']))
    elements.append(Paragraph("This is a test of ReportLab PDF generation.", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Add a table
    data = [
        ['Item', 'Quantity', 'Price'],
        ['Web Design', '5', '$100.00'],
        ['Hosting', '1', '$50.00'],
        ['Domain', '1', '$15.00'],
    ]
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    print(f"✅ PDF generated successfully! Size: {len(pdf_data)} bytes")
    
    # Save to file
    with open('test_reportlab.pdf', 'wb') as f:
        f.write(pdf_data)
    
    print("✅ PDF saved to test_reportlab.pdf")
    return True

if __name__ == '__main__':
    print("Testing ReportLab PDF generation...")
    try:
        success = test_reportlab_pdf()
        if success:
            print("\n✅ ReportLab PDF generation test PASSED")
        else:
            print("\n❌ ReportLab PDF generation test FAILED")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ReportLab PDF generation test FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)