from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse


def faq_view(request):
    """Display the FAQ page."""
    return render(request, 'pages/faq.html')


def contact_view(request):
    """Display the contact page and handle contact form submissions."""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # In a real application, you would send an email or save to database
        # For now, we'll just show a success message
        messages.success(
            request, 
            f'Thank you {name}! Your message has been received. We\'ll get back to you within 24 hours.'
        )
        return HttpResponseRedirect(reverse('contact'))
    
    return render(request, 'pages/contact.html')


def terms_view(request):
    """Display the Terms of Service page."""
    return render(request, 'pages/terms.html')


def privacy_view(request):
    """Display the Privacy Policy page."""
    return render(request, 'pages/privacy.html')


def security_view(request):
    """Display the Security page."""
    return render(request, 'pages/security.html')
