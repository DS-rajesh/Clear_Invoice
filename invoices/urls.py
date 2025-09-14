from django.urls import path
from . import views

urlpatterns = [
    path('invoices/', views.invoice_list_view, name='invoice_list'),
    path('invoices/add/', views.invoice_create_view, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail_view, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_update_view, name='invoice_update'),
    path('invoices/<int:pk>/delete/', views.invoice_delete_view, name='invoice_delete'),
    path('invoices/<int:pk>/pdf/', views.invoice_pdf_view, name='invoice_pdf'),
    path('invoices/<int:pk>/email/', views.invoice_email_view, name='invoice_email'),
    path('invoices/<int:pk>/status/', views.invoice_status_update, name='invoice_status_update'),
    path('invoices/export/csv/', views.invoice_export_csv, name='invoice_export_csv'),
]
