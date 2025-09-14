from django.urls import path
from . import views

urlpatterns = [
    path('clients/', views.client_list_view, name='client_list'),
    path('clients/add/', views.client_create_view, name='client_create'),
    path('clients/<int:pk>/', views.client_detail_view, name='client_detail'),
    path('clients/<int:pk>/edit/', views.client_update_view, name='client_update'),
    path('clients/<int:pk>/delete/', views.client_delete_view, name='client_delete'),
]
