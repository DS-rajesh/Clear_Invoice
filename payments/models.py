from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('other', 'Other'),
    ]
    
    invoice = models.ForeignKey('invoices.Invoice', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment ${self.amount} for {self.invoice.invoice_number}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update invoice status if fully paid
        self.update_invoice_status()
    
    def update_invoice_status(self):
        total_payments = self.invoice.payments.aggregate(
            models.Sum('amount')
        )['amount__sum'] or 0
        
        if total_payments >= self.invoice.total:
            self.invoice.status = 'paid'
        elif total_payments > 0:
            self.invoice.status = 'unpaid'  # Partially paid
        
        self.invoice.save()
