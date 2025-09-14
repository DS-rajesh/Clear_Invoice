from django.contrib import admin
from .models import Invoice, InvoiceItem

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('description', 'quantity', 'unit_price', 'subtotal')
    readonly_fields = ('subtotal',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'client', 'date_issued', 'due_date', 'status', 'total', 'is_sent')
    list_filter = ('status', 'is_sent', 'date_issued', 'due_date')
    search_fields = ('invoice_number', 'client__name', 'client__email')
    ordering = ('-created_at',)
    inlines = [InvoiceItemInline]
    readonly_fields = ('subtotal', 'tax_amount', 'total', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'client', 'invoice_number', 'status')
        }),
        ('Dates', {
            'fields': ('date_issued', 'due_date', 'sent_at')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax_rate', 'tax_amount', 'total')
        }),
        ('Additional Information', {
            'fields': ('notes', 'terms', 'is_sent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('description', 'invoice', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('invoice__status', 'created_at')
    search_fields = ('description', 'invoice__invoice_number')
    readonly_fields = ('subtotal',)
