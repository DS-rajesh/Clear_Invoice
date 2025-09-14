"""
Example Django View Integration for ReportLab PDF Generation.

This module demonstrates how to use the new ReportLab-based PDF generation utility
in various Django view scenarios.
"""

import os
import base64
import zipfile
import tempfile
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
from invoices.models import Invoice
from invoices.utils import generate_pdf, generate_invoice_response

# Example 1: Basic PDF Download View
@login_required
def download_invoice_pdf(request, invoice_id):
    """
    Simple view to download invoice as PDF
    Uses the generate_invoice_response utility for convenience
    """
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)
    
    try:
        # Use the convenience function that handles HTTP response creation
        return generate_invoice_response(invoice)
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('invoice_detail', pk=invoice_id)


# Example 2: PDF Preview in Browser
@login_required
def preview_invoice_pdf(request, invoice_id):
    """
    View to preview PDF in browser (inline display)
    """
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)

    try:
        pdf_data = generate_pdf(invoice)

        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="invoice_{invoice.invoice_number}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('invoice_detail', pk=invoice_id)


# Example 3: Save PDF to File System
@login_required
def save_invoice_pdf(request, invoice_id):
    """
    Save PDF to file system and return file path
    Useful for archiving or batch processing
    """
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)

    try:
        # Create invoices directory if it doesn't exist
        pdf_dir = os.path.join(settings.MEDIA_ROOT, 'invoices', 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)

        # Generate file path
        file_path = os.path.join(pdf_dir, f'invoice_{invoice.invoice_number}.pdf')

        # Generate and save PDF
        saved_path = generate_pdf(invoice, save_to_file=True, file_path=file_path)

        return JsonResponse({
            'success': True,
            'message': 'PDF saved successfully',
            'file_path': saved_path
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# Example 4: Email Invoice with PDF Attachment
@login_required
def email_invoice_pdf(request, invoice_id):
    """
    Email invoice as PDF attachment
    """
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)

    if request.method == 'POST':
        try:
            # Generate PDF
            pdf_data = generate_pdf(invoice)

            # Create email
            email = EmailMessage(
                subject=f'Invoice {invoice.invoice_number}',
                body=f'Please find attached invoice {invoice.invoice_number}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[invoice.client.email],
            )

            # Attach PDF
            email.attach(
                f'invoice_{invoice.invoice_number}.pdf',
                pdf_data,
                'application/pdf'
            )

            # Send email
            email.send()

            # Update invoice status
            invoice.is_sent = True
            invoice.save()

            messages.success(request, f'Invoice {invoice.invoice_number} emailed successfully!')
            return redirect('invoice_detail', pk=invoice_id)

        except Exception as e:
            messages.error(request, f'Error sending email: {str(e)}')

    return render(request, 'invoices/email_form.html', {'invoice': invoice})


# Example 5: Bulk PDF Generation
@login_required
def bulk_generate_pdfs(request):
    """
    Generate PDFs for multiple invoices
    Useful for batch processing
    """
    if request.method == 'POST':
        invoice_ids = request.POST.getlist('invoice_ids')

        try:
            # Create temporary zip file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
                with zipfile.ZipFile(temp_zip, 'w') as zip_file:

                    for invoice_id in invoice_ids:
                        invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)

                        # Generate PDF
                        pdf_data = generate_pdf(invoice)

                        # Add to zip
                        zip_file.writestr(
                            f'invoice_{invoice.invoice_number}.pdf',
                            pdf_data
                        )

                # Return zip file
                with open(temp_zip.name, 'rb') as zip_data:
                    response = HttpResponse(zip_data.read(), content_type='application/zip')
                    response['Content-Disposition'] = 'attachment; filename="invoices.zip"'
                    return response

        except Exception as e:
            messages.error(request, f'Error generating PDFs: {str(e)}')

    # Show form to select invoices
    invoices = Invoice.objects.filter(user=request.user)
    return render(request, 'invoices/bulk_pdf_form.html', {'invoices': invoices})


# Example 6: AJAX PDF Generation
@login_required
def ajax_generate_pdf(request, invoice_id):
    """
    AJAX endpoint for PDF generation
    Returns JSON response with PDF data as base64
    """
    if request.method == 'POST':
        try:
            invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)

            # Generate PDF
            pdf_data = generate_pdf(invoice)

            # Convert to base64 for JSON response
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')

            return JsonResponse({
                'success': True,
                'pdf_data': pdf_base64,
                'filename': f'invoice_{invoice.invoice_number}.pdf'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


# Example URL patterns to add to your urls.py:
"""
from django.urls import path
from . import views

urlpatterns = [
    # ... your existing URLs ...
    
    # PDF Generation URLs
    path('invoice/<int:invoice_id>/download-pdf/', views.download_invoice_pdf, name='download_invoice_pdf'),
    path('invoice/<int:invoice_id>/preview-pdf/', views.preview_invoice_pdf, name='preview_invoice_pdf'),
    path('invoice/<int:invoice_id>/save-pdf/', views.save_invoice_pdf, name='save_invoice_pdf'),
    path('invoice/<int:invoice_id>/email-pdf/', views.email_invoice_pdf, name='email_invoice_pdf'),
    path('invoices/bulk-pdf/', views.bulk_generate_pdfs, name='bulk_generate_pdfs'),
    path('invoice/<int:invoice_id>/ajax-pdf/', views.ajax_generate_pdf, name='ajax_generate_pdf'),
]
"""

# Example JavaScript for AJAX PDF generation:
"""
// Add this to your template
function generatePDF(invoiceId) {
    fetch(`/invoice/${invoiceId}/ajax-pdf/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Create download link
            const link = document.createElement('a');
            link.href = 'data:application/pdf;base64,' + data.pdf_data;
            link.download = data.filename;
            link.click();
        } else {
            alert('Error generating PDF: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error generating PDF');
    });
}
"""
