from django.http import HttpResponse
from django.template.loader import render_to_string
from decimal import Decimal
from datetime import date

def test_pdf_view(request):
    """
    Test view to render the modern PDF template with sample data
    """
    # Sample data for testing
    sample_data = {
        'invoice': {
            'invoice_number': 'INV-2023-001',
            'date_issued': date.today(),
            'due_date': date.today().replace(day=30),
            'tax_rate': Decimal('10.00'),
            'subtotal': Decimal('1000.00'),
            'tax_amount': Decimal('100.00'),
            'total': Decimal('1100.00'),
            'notes': 'Thank you for your business!',
            'terms': 'Payment due within 30 days.',
            'status': 'unpaid',
            'get_status_display': lambda: 'Unpaid',
            'is_overdue': False,
            'items': [
                {
                    'description': 'Web Design Services',
                    'quantity': 10,
                    'unit_price': Decimal('75.00'),
                    'subtotal': Decimal('750.00'),
                },
                {
                    'description': 'Hosting Services',
                    'quantity': 1,
                    'unit_price': Decimal('150.00'),
                    'subtotal': Decimal('150.00'),
                },
                {
                    'description': 'Consulting Services',
                    'quantity': 5,
                    'unit_price': Decimal('40.00'),
                    'subtotal': Decimal('200.00'),
                }
            ],
            'client': {
                'name': 'John Smith',
                'company': 'Acme Corporation',
                'email': 'john@acme.com',
                'address': '123 Business Street\nNew York, NY 10001',
                'phone': '(555) 123-4567',
            }
        },
        'user': {
            'company': 'Your Company Name',
            'get_full_name': lambda: 'Jane Doe',
            'email': 'info@yourcompany.com',
            'address': '456 Corporate Avenue\nLos Angeles, CA 90001',
            'phone': '(555) 987-6543',
        }
    }
    
    # Render the HTML template
    html_content = render_to_string('invoices/invoice_pdf_modern.html', sample_data)
    
    return HttpResponse(html_content, content_type='text/html')