from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import Invoice, InvoiceItem
from .forms import InvoiceForm, InvoiceItemFormSet, InvoiceSearchForm, EmailInvoiceForm
from .utils import generate_pdf
import csv

@login_required
def invoice_list_view(request):
    form = InvoiceSearchForm(request.user, request.GET)
    invoices = Invoice.objects.filter(user=request.user)
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        client = form.cleaned_data.get('client')
        
        if search:
            invoices = invoices.filter(
                Q(invoice_number__icontains=search) |
                Q(client__name__icontains=search) |
                Q(client__email__icontains=search)
            )
        
        if status:
            invoices = invoices.filter(status=status)
        
        if client:
            invoices = invoices.filter(client=client)
    
    paginator = Paginator(invoices, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'invoices': page_obj,
    }
    return render(request, 'invoices/invoice_list.html', context)

@login_required
def invoice_detail_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    context = {
        'invoice': invoice,
    }
    return render(request, 'invoices/invoice_detail.html', context)

@login_required
def invoice_create_view(request):
    if request.method == 'POST':
        form = InvoiceForm(request.user, request.POST)
        formset = InvoiceItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.user = request.user
            invoice.save()
            
            formset.instance = invoice
            formset.save()
            
            # Recalculate totals
            invoice.calculate_totals()
            invoice.save()
            
            messages.success(request, f'Invoice {invoice.invoice_number} created successfully!')
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(request.user)
        formset = InvoiceItemFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Create New Invoice',
    }
    return render(request, 'invoices/invoice_form.html', context)

@login_required
def invoice_update_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = InvoiceForm(request.user, request.POST, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            
            # Recalculate totals
            invoice.calculate_totals()
            invoice.save()
            
            messages.success(request, f'Invoice {invoice.invoice_number} updated successfully!')
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(request.user, instance=invoice)
        formset = InvoiceItemFormSet(instance=invoice)
    
    context = {
        'form': form,
        'formset': formset,
        'invoice': invoice,
        'title': f'Edit Invoice {invoice.invoice_number}',
    }
    return render(request, 'invoices/invoice_form.html', context)

@login_required
def invoice_delete_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    if request.method == 'POST':
        invoice_number = invoice.invoice_number
        invoice.delete()
        messages.success(request, f'Invoice {invoice_number} deleted successfully!')
        return redirect('invoice_list')
    
    context = {
        'invoice': invoice,
    }
    return render(request, 'invoices/invoice_confirm_delete.html', context)

@login_required
def invoice_pdf_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    try:
        pdf_content = generate_pdf(invoice)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('invoice_detail', pk=pk)

@login_required
def invoice_email_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = EmailInvoiceForm(request.POST)
        if form.is_valid():
            try:
                # Generate PDF
                pdf_content = generate_pdf(invoice)
                
                # Create email
                email = EmailMessage(
                    subject=form.cleaned_data['subject'],
                    body=form.cleaned_data['message'],
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[form.cleaned_data['recipient_email']],
                )
                
                # Attach PDF
                email.attach(
                    f'invoice_{invoice.invoice_number}.pdf',
                    pdf_content,
                    'application/pdf'
                )
                
                # Send email
                email.send()
                
                # Update invoice status
                invoice.is_sent = True
                invoice.sent_at = timezone.now()
                if invoice.status == 'draft':
                    invoice.status = 'sent'
                invoice.save()
                
                messages.success(request, f'Invoice {invoice.invoice_number} sent successfully!')
                return redirect('invoice_detail', pk=invoice.pk)
                
            except Exception as e:
                messages.error(request, f'Error sending email: {str(e)}')
    else:
        initial_data = {
            'recipient_email': invoice.client.email,
            'subject': f'Invoice {invoice.invoice_number} from {request.user.company or request.user.get_full_name()}',
            'message': f'''Dear {invoice.client.name},

Please find attached invoice {invoice.invoice_number} for your review.

Invoice Details:
- Invoice Number: {invoice.invoice_number}
- Date Issued: {invoice.date_issued}
- Due Date: {invoice.due_date}
- Total Amount: ${invoice.total}

Thank you for your business!

Best regards,
{request.user.get_full_name() or request.user.username}
{request.user.company or ''}'''
        }
        form = EmailInvoiceForm(initial=initial_data)
    
    context = {
        'form': form,
        'invoice': invoice,
    }
    return render(request, 'invoices/invoice_email.html', context)

@login_required
def invoice_export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="invoices.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Invoice Number', 'Client', 'Date Issued', 'Due Date', 
        'Status', 'Subtotal', 'Tax', 'Total', 'Is Sent'
    ])
    
    invoices = Invoice.objects.filter(user=request.user)
    for invoice in invoices:
        writer.writerow([
            invoice.invoice_number,
            invoice.client.name,
            invoice.date_issued,
            invoice.due_date,
            invoice.get_status_display(),
            invoice.subtotal,
            invoice.tax_amount,
            invoice.total,
            'Yes' if invoice.is_sent else 'No'
        ])
    
    return response

@login_required
def invoice_status_update(request, pk):
    if request.method == 'POST':
        invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
        new_status = request.POST.get('status')
        
        if new_status in dict(Invoice.STATUS_CHOICES):
            invoice.status = new_status
            invoice.save()
            messages.success(request, f'Invoice status updated to {invoice.get_status_display()}')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('invoice_detail', pk=pk)
