"""
Enhanced PDF Generator for Invoices using ReportLab
This module provides improved PDF generation capabilities for invoices.
"""

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from decimal import Decimal
import io
import os
from datetime import datetime


def generate_enhanced_pdf(invoice):
    """
    Generate a professional, enhanced PDF invoice using ReportLab
    
    Args:
        invoice: Invoice model instance
    
    Returns:
        bytes: PDF content
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
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=26,
        spaceAfter=30,
        textColor=colors.HexColor('#2563eb'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    company_style = ParagraphStyle(
        'CompanyInfo',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_RIGHT,
        fontName='Helvetica'
    )
    
    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#2563eb'),
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    right_align_style = ParagraphStyle(
        'RightAlignText',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_RIGHT,
        fontName='Helvetica'
    )
    
    # Header with company info
    user = invoice.user if hasattr(invoice, 'user') and invoice.user else None
    company_name = user.company or (user.get_full_name() if user else 'Your Company')
    company_details = []
    if user:
        if user.address:
            company_details.append(user.address)
        if user.phone:
            company_details.append(f"Phone: {user.phone}")
        if user.email:
            company_details.append(f"Email: {user.email}")
    else:
        company_details.extend([
            "123 Business Street",
            "City, State 12345",
            "Phone: (555) 123-4567",
            "Email: info@company.com"
        ])
    
    # Company information section
    company_info = f"<b>{company_name}</b><br/>" + "<br/>".join(company_details)
    
    # Invoice title
    elements.append(Paragraph("INVOICE", title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(company_info, company_style))
    elements.append(Spacer(1, 20))
    
    # Add horizontal line
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2563eb')))
    elements.append(Spacer(1, 30))
    
    # Invoice details section
    invoice_info_data = [
        [
            Paragraph("<b>BILL TO:</b>", section_heading_style),
            Paragraph("<b>INVOICE DETAILS:</b>", section_heading_style)
        ],
        [
            Paragraph(f"<b>{invoice.client.name}</b><br/>{invoice.client.company or ''}<br/>{invoice.client.address or ''}", normal_style),
            Paragraph(
                f"<b>Invoice #:</b> {invoice.invoice_number}<br/>"
                f"<b>Date Issued:</b> {invoice.date_issued.strftime('%B %d, %Y')}<br/>"
                f"<b>Due Date:</b> {invoice.due_date.strftime('%B %d, %Y')}<br/>"
                f"<b>Status:</b> <font color='{_get_status_color(invoice.status)}'>{invoice.get_status_display().upper()}</font>",
                normal_style
            )
        ]
    ]
    
    info_table = Table(invoice_info_data, colWidths=[3.5*inch, 3.5*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 30))
    
    # Invoice items section
    elements.append(Paragraph("ITEMS", section_heading_style))
    elements.append(Spacer(1, 12))
    
    # Table headers
    items_header = ['DESCRIPTION', 'QTY', 'UNIT PRICE', 'TOTAL']
    items_data = [items_header]
    
    # Add invoice items
    for item in invoice.items.all():
        items_data.append([
            str(item.description),
            str(item.quantity),
            f"${float(item.unit_price):,.2f}",
            f"${float(item.subtotal):,.2f}"
        ])
    
    # Create items table
    items_table = Table(items_data, colWidths=[3.5*inch, 0.75*inch, 1.25*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows styling
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),   # Description left aligned
        ('ALIGN', (1, 1), (1, -1), 'CENTER'), # Quantity centered
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'), # Prices and totals right aligned
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 30))
    
    # Totals section
    totals_data = [
        ['Subtotal:', f"${float(invoice.subtotal):,.2f}"],
        [f'Tax ({float(invoice.tax_rate)}%):', f"${float(invoice.tax_amount):,.2f}"],
        ['Total:', f"${float(invoice.total):,.2f}"]
    ]
    
    totals_table = Table(totals_data, colWidths=[1.5*inch, 2*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 1), (-1, 1), 1, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.white),
        ('FONTSIZE', (0, 2), (-1, 2), 12),
    ]))
    
    # Right-align the totals table
    totals_container = Table([[totals_table]], colWidths=[7*inch])
    totals_container.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (0, 0), 'TOP'),
    ]))
    
    elements.append(totals_container)
    elements.append(Spacer(1, 40))
    
    # Notes and terms section
    if invoice.notes:
        elements.append(Paragraph("NOTES", section_heading_style))
        elements.append(Paragraph(invoice.notes, normal_style))
        elements.append(Spacer(1, 20))
    
    if invoice.terms:
        elements.append(Paragraph("TERMS & CONDITIONS", section_heading_style))
        elements.append(Paragraph(invoice.terms, normal_style))
        elements.append(Spacer(1, 20))
    
    # Add digital signature if available
    if hasattr(invoice, 'user') and invoice.user and invoice.user.digital_signature:
        try:
            signature_path = invoice.user.digital_signature.path
            if os.path.exists(signature_path):
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("AUTHORIZED SIGNATURE", section_heading_style))
                signature = Image(signature_path, width=2*inch, height=0.75*inch)
                elements.append(signature)
                elements.append(Spacer(1, 10))
                elements.append(Paragraph(f"{invoice.user.get_full_name()}", normal_style))
        except:
            pass  # Skip signature if there's an issue loading it
    
    # Footer
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
    elements.append(Spacer(1, 12))
    
    footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Invoice #{invoice.invoice_number}"
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6b7280'),
        alignment=TA_CENTER
    )
    elements.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    doc.build(elements)
    
    # Return PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data


def _get_status_color(status):
    """Helper function to get color for status display"""
    status_colors = {
        'paid': '#10b981',      # green
        'unpaid': '#f59e0b',    # amber
        'overdue': '#ef4444',   # red
        'draft': '#6b7280',     # gray
        'sent': '#3b82f6',      # blue
        'cancelled': '#6b7280'  # gray
    }
    
    return status_colors.get(status, "#6b7280")


def generate_invoice_response(invoice, filename=None):
    """
    Generate HTTP response with PDF invoice
    
    Args:
        invoice: Invoice model instance
        filename: Optional filename for download
    
    Returns:
        HttpResponse: PDF response for download
    """
    if not filename:
        filename = f"invoice_{invoice.invoice_number}.pdf"
    
    try:
        pdf_data = generate_enhanced_pdf(invoice)
    except Exception as e:
        raise Exception(f"Error generating PDF: {str(e)}")
    
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Length'] = len(pdf_data)
    
    return response