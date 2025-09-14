from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'payment_date', 'payment_method', 'reference_number')
    list_filter = ('payment_method', 'payment_date', 'created_at')
    search_fields = ('invoice__invoice_number', 'reference_number', 'invoice__client__name')
    ordering = ('-payment_date',)
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('invoice', 'amount', 'payment_date', 'payment_method')
        }),
        ('Additional Details', {
            'fields': ('reference_number', 'notes')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(invoice__user=request.user)
