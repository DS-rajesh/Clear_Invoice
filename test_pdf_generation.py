#!/usr/bin/env python
"""
Test script to verify PDF generation functionality works correctly
after removing WeasyPrint and using only ReportLab.
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'invoicely.settings')
django.setup()

from invoices.utils import generate_pdf
from invoices.models import Invoice, InvoiceItem
from clients.models import Client
from users.models import User
from datetime import date
from decimal import Decimal
import tempfile

def create_test_data():
    """Create test data for PDF generation"""
    # Create a test user
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'company': 'Test Company'
        }
    )
    
    # Create a test client
    client, created = Client.objects.get_or_create(
        user=user,
        email='client@example.com',
        defaults={
            'name': 'Test Client',
            'company': 'Client Company',
            'address': '123 Client Street',
            'city': 'Client City',
            'state': 'Client State',
            'zip_code': '12345',
            'country': 'Client Country'
        }
    )
    
    # Create a test invoice
    invoice, created = Invoice.objects.get_or_create(
        user=user,
        client=client,
        invoice_number='INV-2024-001',
        defaults={
            'date_issued': date.today(),
            'due_date': date.today(),
            'status': 'draft',
            'tax_rate': Decimal('10.00')
        }
    )
    
    # Create test invoice items
    items_data = [
        {'description': 'Web Design Service', 'quantity': 5, 'unit_price': 100},
        {'description': 'Hosting Service', 'quantity': 1, 'unit_price': 50},
        {'description': 'Domain Registration', 'quantity': 1, 'unit_price': 15},
    ]
    
    # Clear existing items if recreating
    if not created:
        invoice.items.all().delete()
    
    for item_data in items_data:
        InvoiceItem.objects.create(
            invoice=invoice,
            description=item_data['description'],
            quantity=item_data['quantity'],
            unit_price=item_data['unit_price']
        )
    
    # Recalculate totals
    invoice.calculate_totals()
    invoice.save()
    
    return invoice

def test_pdf_generation():
    """Test PDF generation functionality"""
    print("Creating test data...")
    invoice = create_test_data()
    
    print(f"Created invoice: {invoice.invoice_number}")
    print(f"Invoice items: {invoice.items.count()}")
    print(f"Subtotal: ${invoice.subtotal}")
    print(f"Tax: ${invoice.tax_amount}")
    print(f"Total: ${invoice.total}")
    
    print("\nGenerating PDF...")
    try:
        pdf_data = generate_pdf(invoice)
        print(f"PDF generated successfully! Size: {len(pdf_data)} bytes")
        
        # Save to file for verification
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_data)
            print(f"PDF saved to: {tmp_file.name}")
            
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Testing PDF generation functionality...")
    success = test_pdf_generation()
    if success:
        print("\n✅ PDF generation test PASSED")
    else:
        print("\n❌ PDF generation test FAILED")
    sys.exit(0 if success else 1)