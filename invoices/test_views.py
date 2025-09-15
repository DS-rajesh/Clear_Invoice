from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .forms import InvoiceForm, InvoiceItemFormSet

@login_required
def test_invoice_form_modern(request):
    """
    Test view for the modern invoice creation form
    """
    form = InvoiceForm(request.user)
    formset = InvoiceItemFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Test Modern Invoice Form',
    }
    return render(request, 'invoices/invoice_form_modern.html', context)