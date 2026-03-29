from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.core.cache import cache
import json
import csv
from datetime import datetime

from .models import Invoice, InvoiceItem
from .forms import InvoiceForm, InvoiceItemFormSet, InvoiceSearchForm, EmailInvoiceForm
from .pdf_generator import generate_enhanced_pdf
from clients.models import Client


# ============================
# 🔹 HELPERS (REUSABLE LOGIC)
# ============================

def get_user_invoices(user):
    return (
        Invoice.objects
        .filter(user=user)
        .select_related('client', 'user')
        .prefetch_related('items')
    )


def apply_invoice_filters(queryset, search=None, status=None, client=None):
    if search:
        queryset = queryset.filter(
            Q(invoice_number__icontains=search) |
            Q(client__name__icontains=search) |
            Q(client__email__icontains=search)
        )
    if status:
        queryset = queryset.filter(status=status)
    if client:
        queryset = queryset.filter(client=client)

    return queryset


def save_invoice_with_items(form, formset, user):
    invoice = form.save(commit=False)
    invoice.user = user
    invoice.save()

    formset.instance = invoice
    items = formset.save(commit=False)

    for item in items:
        item.invoice = invoice
        item.save()

    for obj in formset.deleted_objects:
        obj.delete()

    invoice.calculate_totals()
    invoice.save()

    return invoice


# ============================
# 🔹 VIEWS
# ============================

@login_required
@cache_page(60)
def invoice_list_view(request):
    form = InvoiceSearchForm(request.user, request.GET)
    invoices = get_user_invoices(request.user)

    if form.is_valid():
        invoices = apply_invoice_filters(
            invoices,
            form.cleaned_data.get('search'),
            form.cleaned_data.get('status'),
            form.cleaned_data.get('client')
        )

    paginator = Paginator(invoices, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'invoices/invoice_list.html', {
        'form': form,
        'page_obj': page_obj,
        'invoices': page_obj,
    })


@login_required
def invoice_detail_view(request, pk):
    invoice = get_object_or_404(get_user_invoices(request.user), pk=pk)
    return render(request, 'invoices/invoice_detail.html', {'invoice': invoice})


@login_required
def invoice_create_view(request):
    form = InvoiceForm(request.user, request.POST or None)
    formset = InvoiceItemFormSet(request.POST or None)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        invoice = save_invoice_with_items(form, formset, request.user)
        messages.success(request, f'Invoice {invoice.invoice_number} created!')
        return redirect('invoice_detail', pk=invoice.pk)

    return render(request, 'invoices/invoice_form_enhanced.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Invoice',
    })


@login_required
def invoice_update_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)

    form = InvoiceForm(request.user, request.POST or None, instance=invoice)
    formset = InvoiceItemFormSet(request.POST or None, instance=invoice)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        save_invoice_with_items(form, formset, request.user)
        messages.success(request, f'Invoice {invoice.invoice_number} updated!')
        return redirect('invoice_detail', pk=invoice.pk)

    return render(request, 'invoices/invoice_form.html', {
        'form': form,
        'formset': formset,
        'invoice': invoice,
        'title': f'Edit {invoice.invoice_number}',
    })


@login_required
def invoice_delete_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)

    if request.method == 'POST':
        invoice.delete()
        messages.success(request, 'Invoice deleted!')
        return redirect('invoice_list')

    return render(request, 'invoices/invoice_confirm_delete.html', {'invoice': invoice})


@login_required
def invoice_pdf_view(request, pk):
    invoice = get_object_or_404(get_user_invoices(request.user), pk=pk)

    cache_key = f"invoice_pdf:{invoice.pk}:{int(invoice.updated_at.timestamp())}"
    pdf = cache.get(cache_key)

    if not pdf:
        pdf = generate_enhanced_pdf(invoice)
        cache.set(cache_key, pdf, 300)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=invoice_{invoice.invoice_number}.pdf'
    return response


@login_required
def invoice_email_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)

    form = EmailInvoiceForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        try:
            pdf = generate_enhanced_pdf(invoice)

            email = EmailMessage(
                subject=form.cleaned_data['subject'],
                body=form.cleaned_data['message'],
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[form.cleaned_data['recipient_email']],
            )

            email.attach(f'invoice_{invoice.invoice_number}.pdf', pdf, 'application/pdf')
            email.send()

            invoice.is_sent = True
            invoice.sent_at = timezone.now()
            invoice.status = 'sent' if invoice.status == 'draft' else invoice.status
            invoice.save()

            messages.success(request, 'Invoice sent!')
            return redirect('invoice_detail', pk=invoice.pk)

        except Exception as e:
            messages.error(request, str(e))

    return render(request, 'invoices/invoice_email.html', {
        'form': form,
        'invoice': invoice
    })


@login_required
def invoice_export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=invoices.csv'

    writer = csv.writer(response)
    writer.writerow(['Invoice', 'Client', 'Issued', 'Due', 'Status', 'Total'])

    invoices = get_user_invoices(request.user)

    for inv in invoices:
        writer.writerow([
            inv.invoice_number,
            inv.client.name,
            inv.date_issued,
            inv.due_date,
            inv.get_status_display(),
            inv.total
        ])

    return response


# ============================
# 🔹 API VIEWS
# ============================

@login_required
def api_invoice_list_view(request):
    queryset = get_user_invoices(request.user)

    queryset = apply_invoice_filters(
        queryset,
        request.GET.get('search'),
        request.GET.get('status'),
        request.GET.get('client')
    )

    paginator = Paginator(queryset, int(request.GET.get('page_size', 20)))
    page = paginator.get_page(request.GET.get('page'))

    data = [
        {
            'id': inv.id,
            'invoice_number': inv.invoice_number,
            'client': inv.client.name,
            'total': str(inv.total),
        } for inv in page
    ]

    return JsonResponse({
        'results': data,
        'total': paginator.count
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_invoice_create_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Auth required'}, status=401)

    try:
        data = json.loads(request.body)

        client = Client.objects.get(id=data['client_id'], user=request.user)

        invoice = Invoice.objects.create(
            user=request.user,
            client=client,
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d'),
        )

        for item in data.get('items', []):
            InvoiceItem.objects.create(
                invoice=invoice,
                description=item['description'],
                quantity=item.get('quantity', 1),
                unit_price=item['unit_price']
            )

        invoice.calculate_totals()
        invoice.save()

        return JsonResponse({'success': True, 'id': invoice.id})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
