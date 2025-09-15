from django.http import HttpResponse
from django.conf import settings
from django.template.loader import render_to_string
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from decimal import Decimal
import io
import os
from datetime import datetime

# Optional WeasyPrint import for HTML-based PDF generation
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

def generate_pdf_html(invoice):
    """
    Generate PDF invoice using HTML template and WeasyPrint
    
    Args:
        invoice: Invoice model instance
    
    Returns:
        bytes: PDF content
    """
    if not WEASYPRINT_AVAILABLE:
        raise ImportError("WeasyPrint is not available. Please install required system dependencies.")
    
    # Render the HTML template with invoice data
    html_content = render_to_string('invoices/invoice_pdf_template.html', {
        'invoice': invoice,
        'user': invoice.user if hasattr(invoice, 'user') else None,
    })
    
    # Generate PDF from HTML
    font_config = FontConfiguration()
    html = HTML(string=html_content, base_url=settings.MEDIA_URL)
    pdf_bytes = html.write_pdf(font_config=font_config)
    
    return pdf_bytes


def generate_pdf(invoice, save_to_file=False, file_path=None):
    """
    Generate professional PDF invoice using ReportLab (Legacy)
    
    Args:
        invoice: Invoice model instance
        save_to_file: Boolean, if True saves to file, otherwise returns bytes
        file_path: Optional file path to save PDF (if save_to_file=True)
    
    Returns:
        bytes: PDF content if save_to_file=False
        str: File path if save_to_file=True
    """
    
    # Create a BytesIO buffer to hold PDF data
    buffer = io.BytesIO()
    
    # Create the PDF document with A4 page size and margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    # Container for the 'Flowable' objects (content elements)
    elements = []
    
    # Define custom styles
    styles = getSampleStyleSheet()
    
    # Custom styles for the invoice
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#4f46e5'),
        alignment=TA_LEFT
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#4f46e5'),
        alignment=TA_LEFT
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_LEFT
    )
    
    right_align_style = ParagraphStyle(
        'RightAlign',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_RIGHT
    )
    
    # Add company logo if it exists
    if hasattr(invoice, 'user') and invoice.user and invoice.user.logo:
        try:
            logo_path = invoice.user.logo.path
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=2*inch, height=1*inch)
                elements.append(logo)
                elements.append(Spacer(1, 12))
        except:
            pass  # Skip logo if there's an issue loading it
    
    # Invoice title and company info section
    user = invoice.user if hasattr(invoice, 'user') and invoice.user else None
    company_info = f"<b>{user.company or user.get_full_name() if user else 'Your Company'}</b><br/>"
    if user and user.address:
        company_info += f"{user.address}<br/>"
    if user and user.phone:
        company_info += f"Phone: {user.phone}<br/>"
    if user and user.email:
        company_info += f"Email: {user.email}"
    else:
        company_info += "123 Business Street<br/>City, State 12345<br/>Phone: (555) 123-4567<br/>Email: info@company.com"
    
    header_data = [
        [
            Paragraph("INVOICE", title_style),
            Paragraph(company_info, right_align_style)
        ]
    ]
    
    header_table = Table(header_data, colWidths=[3*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Add horizontal line
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#4f46e5')))
    elements.append(Spacer(1, 20))
    
    # Invoice and client information section
    invoice_info_data = [
        [
            Paragraph("<b>Bill To:</b>", heading_style),
            Paragraph("<b>Invoice Details:</b>", heading_style)
        ],
        [
            Paragraph(f"<b>{invoice.client.name}</b><br/>{invoice.client.company or ''}<br/>{invoice.client.address or ''}<br/>{invoice.client.city or ''}, {invoice.client.state or ''} {invoice.client.zip_code or ''}<br/>{invoice.client.country or ''}<br/>Email: {invoice.client.email}", normal_style),
            Paragraph(f"<b>Invoice #:</b> {invoice.invoice_number}<br/><b>Date Issued:</b> {invoice.date_issued.strftime('%B %d, %Y')}<br/><b>Due Date:</b> {invoice.due_date.strftime('%B %d, %Y')}<br/><b>Status:</b> {_get_status_display(invoice.status)}", normal_style)
        ]
    ]
    
    info_table = Table(invoice_info_data, colWidths=[3*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 30))
    
    # Invoice items table
    elements.append(Paragraph("Invoice Items", heading_style))
    elements.append(Spacer(1, 12))
    
    # Table headers
    items_data = [
        ['Description', 'Quantity', 'Unit Price', 'Subtotal']
    ]
    
    # Add invoice items
    for item in invoice.items.all():
        items_data.append([
            str(item.description),
            str(item.quantity),
            f"${item.unit_price:,.2f}",
            f"${item.subtotal:,.2f}"
        ])
    
    # Create items table
    items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1.25*inch, 1.25*inch])
    items_table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),  # Right align numbers
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows styling
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        
        # Border styling
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ddd')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 30))
    
    # Totals section (right-aligned)
    totals_data = [
        ['Subtotal:', f"${invoice.subtotal:,.2f}"],
        [f'Tax ({invoice.tax_rate}%):', f"${invoice.tax_amount:,.2f}"],
        ['Total:', f"${invoice.total:,.2f}"]
    ]
    
    totals_table = Table(totals_data, colWidths=[1.5*inch, 1.25*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 1), (-1, 1), 1, colors.HexColor('#ddd')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.white),
        ('FONTSIZE', (0, 2), (-1, 2), 12),
    ]))
    
    # Create a table to right-align the totals table
    totals_container = Table([[totals_table]], colWidths=[6.5*inch])
    totals_container.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (0, 0), 'TOP'),
    ]))
    
    elements.append(totals_container)
    elements.append(Spacer(1, 40))
    
    # Notes and terms section
    if invoice.notes:
        elements.append(Paragraph("Notes:", heading_style))
        elements.append(Paragraph(invoice.notes, normal_style))
        elements.append(Spacer(1, 20))
    
    if invoice.terms:
        elements.append(Paragraph("Terms & Conditions:", heading_style))
        elements.append(Paragraph(invoice.terms, normal_style))
        elements.append(Spacer(1, 20))
    
    # Add digital signature if available
    if hasattr(invoice, 'user') and invoice.user and invoice.user.digital_signature:
        try:
            signature_path = invoice.user.digital_signature.path
            if os.path.exists(signature_path):
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("Authorized Signature:", heading_style))
                signature = Image(signature_path, width=2*inch, height=0.75*inch)
                elements.append(signature)
                elements.append(Spacer(1, 10))
                elements.append(Paragraph(f"{invoice.user.get_full_name()}", normal_style))
        except:
            pass  # Skip signature if there's an issue loading it
    
    # Footer
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#ddd')))
    elements.append(Spacer(1, 12))
    
    footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Invoice #{invoice.invoice_number}"
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#666'),
        alignment=TA_CENTER
    )
    elements.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    doc.build(elements)
    
    # Handle return value based on save_to_file parameter
    if save_to_file:
        if not file_path:
            file_path = f"invoice_{invoice.invoice_number}.pdf"
        
        with open(file_path, 'wb') as f:
            f.write(buffer.getvalue())
        buffer.close()
        return file_path
    else:
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data


def _get_status_display(status):
    """Helper function to get colored status display"""
    status_colors = {
        'paid': '#10b981',
        'unpaid': '#f59e0b', 
        'overdue': '#ef4444',
        'draft': '#6b7280',
        'sent': '#3b82f6',
        'cancelled': '#6b7280'
    }
    
    return f'<font color="{status_colors.get(status, "#6b7280")}">{status.upper()}</font>'


def generate_invoice_response(invoice, filename=None):
    """
    Generate HTTP response with PDF invoice using ReportLab
    
    Args:
        invoice: Invoice model instance
        filename: Optional filename for download
    
    Returns:
        HttpResponse: PDF response for download
    """
    if not filename:
        filename = f"invoice_{invoice.invoice_number}.pdf"
    
    try:
        pdf_data = generate_pdf(invoice)
    except Exception as e:
        raise Exception(f"Error generating PDF: {str(e)}")
    
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Length'] = len(pdf_data)
    
    return response
