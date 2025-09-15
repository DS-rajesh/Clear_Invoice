from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Test the new invoice templates by rendering them to files'

    def handle(self, *args, **options):
        # Create test output directory
        output_dir = os.path.join(settings.BASE_DIR, 'test_output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Test data
        test_context = {
            'title': 'Test Invoice',
            'form': None,  # In a real test, you would create actual form instances
            'formset': None,
        }
        
        try:
            # Test modern invoice form template
            html_content = render_to_string('invoices/invoice_form_modern.html', test_context)
            form_path = os.path.join(output_dir, 'test_invoice_form_modern.html')
            with open(form_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully rendered modern invoice form to {form_path}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error rendering modern invoice form: {str(e)}')
            )
        
        try:
            # Test modern PDF template
            pdf_context = {
                'invoice': None,  # In a real test, you would create an actual invoice instance
                'user': None,
            }
            html_content = render_to_string('invoices/invoice_pdf_modern.html', pdf_context)
            pdf_path = os.path.join(output_dir, 'test_invoice_pdf_modern.html')
            with open(pdf_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully rendered modern PDF template to {pdf_path}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error rendering modern PDF template: {str(e)}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Template testing completed. Check the test_output directory.')
        )