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
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
import json
from .models import Invoice, InvoiceItem
from .forms import InvoiceForm, InvoiceItemFormSet, InvoiceSearchForm, EmailInvoiceForm
from .pdf_generator import generate_enhanced_pdf, generate_invoice_response
from clients.models import Client
import csv


from django.views.decorators.cache import cache_page
from django.core.cache import cache


@login_required
@cache_page(60)
def invoice_list_view(request):
    form = InvoiceSearchForm(request.user, request.GET)
    invoices = (
        Invoice.objects
        .filter(user=request.user)
        .select_related('client')
        .prefetch_related('items')
    )
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        client = form.cleaned_data.get('client')
        
        if search:
            invoices = invoices.filter(
                Q(invoice_number__icontains=search) |  # type: ignore
                Q(client__name__icontains=search) |  # type: ignore
                Q(client__email__icontains=search)  # type: ignore
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
@cache_page(60)
def invoice_detail_view(request, pk):
    invoice = (
        Invoice.objects
        .select_related('client', 'user')
        .prefetch_related('items')
        .filter(user=request.user, pk=pk)
        .first()
    )
    if not invoice:
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
            instances = formset.save(commit=False)
            
            # Save each item and calculate subtotal
            for instance in instances:
                instance.invoice = invoice
                instance.save()
            
            # Handle deletions
            for obj in formset.deleted_objects:
                obj.delete()
            
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
    return render(request, 'invoices/invoice_form_enhanced.html', context)

@login_required
def invoice_update_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = InvoiceForm(request.user, request.POST, instance=invoice)
        formset = InvoiceItemFormSet(request.POST, instance=invoice)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            instances = formset.save(commit=False)
            
            # Save each item
            for instance in instances:
                instance.invoice = invoice
                instance.save()
            
            # Handle deletions
            for obj in formset.deleted_objects:
                obj.delete()
            
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
    invoice = (
        Invoice.objects
        .select_related('client', 'user')
        .prefetch_related('items')
        .filter(user=request.user, pk=pk)
        .first()
    )
    if not invoice:
        invoice = get_object_or_404(Invoice, pk=pk, user=request.user)

    cache_key = f"invoice_pdf:{invoice.pk}:{int(invoice.updated_at.timestamp())}"
    pdf_content = cache.get(cache_key)
    try:
        if not pdf_content:
            pdf_content = generate_enhanced_pdf(invoice)
            cache.set(cache_key, pdf_content, timeout=300)
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
                # Generate PDF using the new enhanced method
                pdf_content = generate_enhanced_pdf(invoice)
                
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
    
    invoices = (
        Invoice.objects
        .filter(user=request.user)
        .select_related('client')
        .only('invoice_number', 'date_issued', 'due_date', 'status', 'subtotal', 'tax_amount', 'total', 'is_sent', 'client__name')
    )
    for invoice in invoices:
        writer.writerow([
            invoice.invoice_number,
            invoice.client.name,
            invoice.date_issued,
            invoice.due_date,
            invoice.get_status_display(),
            str(invoice.subtotal),
            str(invoice.tax_amount),
            str(invoice.total),
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


@login_required
def api_invoice_list_view(request):
    search = request.GET.get('search')
    status = request.GET.get('status')
    client_id = request.GET.get('client')
    page_size = int(request.GET.get('page_size') or 20)
    page_number = request.GET.get('page')

    queryset = (
        Invoice.objects
        .filter(user=request.user)
        .select_related('client')
        .only('id', 'invoice_number', 'date_issued', 'due_date', 'status', 'total', 'client__name')
    )

    if search:
        queryset = queryset.filter(
            Q(invoice_number__icontains=search) |
            Q(client__name__icontains=search) |
            Q(client__email__icontains=search)
        )
    if status:
        queryset = queryset.filter(status=status)
    if client_id:
        queryset = queryset.filter(client_id=client_id)

    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page_number)

    data = [
        {
            'id': inv.id,
            'invoice_number': inv.invoice_number,
            'client_name': inv.client.name,
            'date_issued': inv.date_issued.isoformat(),
            'due_date': inv.due_date.isoformat(),
            'status': inv.status,
            'total': str(inv.total),
        }
        for inv in page_obj
    ]

    return JsonResponse({
        'results': data,
        'page': page_obj.number,
        'num_pages': paginator.num_pages,
        'total': paginator.count,
        'page_size': page_obj.paginator.per_page,
    })

@csrf_exempt
@require_http_methods(["POST"])
def api_invoice_create_view(request):
    """
    API endpoint for creating invoices with JSON data
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['client_id', 'due_date']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Get user (assuming authenticated user)
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
        
        user = request.user
        
        # Get client
        try:
            client = Client.objects.get(id=data.get('client_id'), user=user)
        except Client.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Client not found'
            }, status=400)
        
        # Validate date fields
        try:
            from datetime import datetime
            date_issued = data.get('date_issued')
            if date_issued:
                date_issued = datetime.strptime(date_issued, '%Y-%m-%d').date()
            else:
                date_issued = timezone.now().date()
                
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=400)
        
        # Create invoice
        invoice = Invoice.objects.create(
            user=user,
            client=client,
            date_issued=date_issued,
            due_date=due_date,
            tax_rate=data.get('tax_rate', 0),
            notes=data.get('notes', ''),
            terms=data.get('terms', ''),
            status=data.get('status', 'draft')
        )
        
        # Create invoice items
        items_data = data.get('items', [])
        if not items_data:
            return JsonResponse({
                'success': False,
                'error': 'At least one invoice item is required'
            }, status=400)
            
        created_items = []
        for item_data in items_data:
            # Validate required item fields
            if not item_data.get('description') or not item_data.get('unit_price'):
                return JsonResponse({
                    'success': False,
                    'error': 'Each item must have description and unit_price'
                }, status=400)
                
            item = InvoiceItem.objects.create(
                invoice=invoice,
                description=item_data.get('description'),
                quantity=item_data.get('quantity', 1),
                unit_price=item_data.get('unit_price', 0)
            )
            created_items.append(item)
        
        # Calculate totals
        invoice.calculate_totals()
        invoice.save()
        
        return JsonResponse({
            'success': True,
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'message': f'Invoice {invoice.invoice_number} created successfully!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
