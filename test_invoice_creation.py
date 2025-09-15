"""
Test script to verify invoice creation functionality
"""
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'invoicely.settings')
django.setup()

from django.contrib.auth import get_user_model
from clients.models import Client
from invoices.models import Invoice, InvoiceItem

# Get user model
User = get_user_model()

def test_invoice_creation():
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Get or create a test client
    client, created = Client.objects.get_or_create(
        user=user,
        email='client@example.com',
        defaults={
            'name': 'Test Client',
            'company': 'Test Company'
        }
    )
    
    # Create an invoice
    invoice = Invoice.objects.create(
        user=user,
        client=client,
        invoice_number='INV-2024-001',
        due_date='2024-12-31'
    )
    
    # Create invoice items
    item1 = InvoiceItem.objects.create(
        invoice=invoice,
        description='Web Design Services',
        quantity=5,
        unit_price=100.00
    )
    
    item2 = InvoiceItem.objects.create(
        invoice=invoice,
        description='Hosting Services',
        quantity=1,
        unit_price=50.00
    )
    
    # Calculate totals
    invoice.calculate_totals()
    invoice.save()
    
    print(f"Invoice created: {invoice.invoice_number}")
    print(f"Client: {invoice.client.name}")
    print(f"Subtotal: ${invoice.subtotal}")
    print(f"Tax Amount: ${invoice.tax_amount}")
    print(f"Total: ${invoice.total}")
    print(f"Items:")
    for item in invoice.items.all():
        print(f"  - {item.description}: {item.quantity} x ${item.unit_price} = ${item.subtotal}")
    
    return invoice

if __name__ == '__main__':
    test_invoice_creation()