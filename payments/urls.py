from django.urls import path
from . import views

urlpatterns = [
    path('payments/', views.payment_list_view, name='payment_list'),
    path('payments/add/', views.payment_create_view, name='payment_create'),
    path('payments/<int:pk>/', views.payment_detail_view, name='payment_detail'),
    path('payments/<int:pk>/edit/', views.payment_update_view, name='payment_update'),
    path('payments/<int:pk>/delete/', views.payment_delete_view, name='payment_delete'),
]
