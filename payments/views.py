from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from .models import Payment
from .forms import PaymentForm, PaymentSearchForm
from invoices.models import Invoice

@login_required
def payment_list_view(request):
    form = PaymentSearchForm(request.GET)
    payments = Payment.objects.filter(invoice__user=request.user)
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        payment_method = form.cleaned_data.get('payment_method')
        
        if search:
            payments = payments.filter(
                Q(invoice__invoice_number__icontains=search) |
                Q(invoice__client__name__icontains=search) |
                Q(reference_number__icontains=search)
            )
        
        if payment_method:
            payments = payments.filter(payment_method=payment_method)
    
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate totals
    total_payments = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'payments': page_obj,
        'total_payments': total_payments,
    }
    return render(request, 'payments/payment_list.html', context)

@login_required
def payment_detail_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk, invoice__user=request.user)
    
    context = {
        'payment': payment,
    }
    return render(request, 'payments/payment_detail.html', context)

@login_required
def payment_create_view(request):
    if request.method == 'POST':
        form = PaymentForm(request.user, request.POST)
        if form.is_valid():
            payment = form.save()
            messages.success(request, f'Payment of ${payment.amount} recorded successfully!')
            return redirect('payment_detail', pk=payment.pk)
    else:
        # Pre-fill invoice if provided in URL
        invoice_id = request.GET.get('invoice')
        initial = {}
        if invoice_id:
            try:
                invoice = Invoice.objects.get(pk=invoice_id, user=request.user)
                initial['invoice'] = invoice
                # Calculate remaining balance
                paid_amount = invoice.payments.aggregate(Sum('amount'))['amount__sum'] or 0
                remaining = invoice.total - paid_amount
                if remaining > 0:
                    initial['amount'] = remaining
            except Invoice.DoesNotExist:
                pass
        
        form = PaymentForm(request.user, initial=initial)
    
    context = {
        'form': form,
        'title': 'Record New Payment',
    }
    return render(request, 'payments/payment_form.html', context)

@login_required
def payment_update_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk, invoice__user=request.user)
    
    if request.method == 'POST':
        form = PaymentForm(request.user, request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment updated successfully!')
            return redirect('payment_detail', pk=payment.pk)
    else:
        form = PaymentForm(request.user, instance=payment)
    
    context = {
        'form': form,
        'payment': payment,
        'title': f'Edit Payment #{payment.pk}',
    }
    return render(request, 'payments/payment_form.html', context)

@login_required
def payment_delete_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk, invoice__user=request.user)
    
    if request.method == 'POST':
        invoice = payment.invoice
        payment.delete()
        # Update invoice status after payment deletion
        payment.update_invoice_status()
        messages.success(request, 'Payment deleted successfully!')
        return redirect('payment_list')
    
    context = {
        'payment': payment,
    }
    return render(request, 'payments/payment_confirm_delete.html', context)
