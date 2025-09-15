from django.urls import path
from . import views
from . import product_service_views

urlpatterns = [
    path('invoices/', views.invoice_list_view, name='invoice_list'),
    path('invoices/add/', views.invoice_create_view, name='invoice_create'),
    path('api/invoices/add/', views.api_invoice_create_view, name='api_invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail_view, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_update_view, name='invoice_update'),
    path('invoices/<int:pk>/delete/', views.invoice_delete_view, name='invoice_delete'),
    path('invoices/<int:pk>/pdf/', views.invoice_pdf_view, name='invoice_pdf'),
    path('invoices/<int:pk>/email/', views.invoice_email_view, name='invoice_email'),
    path('invoices/<int:pk>/status/', views.invoice_status_update, name='invoice_status_update'),
    path('invoices/export/csv/', views.invoice_export_csv, name='invoice_export_csv'),
    
    # Product/Service URLs
    path('products/', product_service_views.product_service_list_view, name='product_service_list'),
    path('products/add/', product_service_views.product_service_create_view, name='product_service_create'),
    path('products/<int:pk>/edit/', product_service_views.product_service_update_view, name='product_service_update'),
    path('products/<int:pk>/delete/', product_service_views.product_service_delete_view, name='product_service_delete'),
    path('api/products/lookup/', product_service_views.product_service_lookup_view, name='product_service_lookup'),
]