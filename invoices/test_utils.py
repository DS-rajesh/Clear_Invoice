from django.template.loader import render_to_string
from django.http import HttpResponse
from .models import Invoice, InvoiceItem
from clients.models import Client
from django.contrib.auth import get_user_model
from datetime import date
from decimal import Decimal

def test_pdf_template(request):
    """
    Test view for the modern PDF template
    """
    # Create a test invoice with sample data
    User = get_user_model()
    
    # Create a test user if one doesn't exist
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'company': 'Test Company',
            'address': '123 Test Street\nTest City, TS 12345',
            'phone': '(555) 123-4567',
        }
    )
    
    # Create a test client if one doesn't exist
    client, created = Client.objects.get_or_create(
        name='Test Client',
        user=user,
        defaults={
            'company': 'Client Company',
            'email': 'client@example.com',
            'address': '456 Client Avenue\nClient City, CC 67890',
            'phone': '(555) 987-6543',
        }
    )
    
    # Create a test invoice
    invoice, created = Invoice.objects.get_or_create(
        invoice_number='INV-2023-001',
        user=user,
        client=client,
        defaults={
            'date_issued': date.today(),
            'due_date': date.today().replace(day=30),
            'tax_rate': Decimal('10.00'),
            'notes': 'Thank you for your business!',
            'terms': 'Payment due within 30 days.',
            'status': 'unpaid',
        }
    )
    
    # Create test invoice items
    if not invoice.items.exists():
        InvoiceItem.objects.create(
            invoice=invoice,
            description='Web Design Services',
            quantity=Decimal('10'),
            unit_price=Decimal('75.00')
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description='Hosting Services',
            quantity=Decimal('1'),
            unit_price=Decimal('150.00')
        )
    
    # Calculate totals
    invoice.calculate_totals()
    
    # Render the HTML template
    html_content = render_to_string('invoices/invoice_pdf_modern.html', {
        'invoice': invoice,
        'user': user,
    })
    
    return HttpResponse(html_content, content_type='text/html')