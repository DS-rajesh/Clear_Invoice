from django.urls import path
from . import views

urlpatterns = [
    path('faq/', views.faq_view, name='faq'),
    path('contact/', views.contact_view, name='contact'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('security/', views.security_view, name='security'),
]
