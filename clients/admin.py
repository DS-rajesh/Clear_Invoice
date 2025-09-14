from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'company', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'country')
    search_fields = ('name', 'email', 'company', 'phone')
    ordering = ('-created_at',)
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'email', 'phone', 'company')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'zip_code', 'country')
        }),
        ('Additional Information', {
            'fields': ('tax_number', 'notes', 'is_active')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
