from django.contrib.auth.models import AbstractUser
from django.db import models

def user_logo_upload_path(instance, filename):
    """Generate upload path for user logos"""
    return f'logos/{instance.id}/{filename}'

def user_signature_upload_path(instance, filename):
    """Generate upload path for user digital signatures"""
    return f'signatures/{instance.id}/{filename}'

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('client', 'Client'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=20, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to=user_logo_upload_path, blank=True, null=True, help_text="Company logo for invoices")
    digital_signature = models.ImageField(upload_to=user_signature_upload_path, blank=True, null=True, help_text="Digital signature for invoices")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    class Meta:
        db_table = 'users'
