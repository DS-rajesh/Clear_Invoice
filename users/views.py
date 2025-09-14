from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from invoices.models import Invoice
from clients.models import Client

def landing_view(request):
    """Landing page for the invoicing application"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'users/landing.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Invoicely!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password. Please try again.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def dashboard_view(request):
    # Get statistics for the dashboard
    total_invoices = Invoice.objects.filter(user=request.user).count()
    paid_invoices = Invoice.objects.filter(user=request.user, status='paid').count()
    unpaid_invoices = Invoice.objects.filter(user=request.user, status='unpaid').count()
    overdue_invoices = Invoice.objects.filter(
        user=request.user, 
        status='unpaid', 
        due_date__lt=timezone.now().date()
    ).count()
    
    total_revenue = Invoice.objects.filter(
        user=request.user, 
        status='paid'
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    pending_revenue = Invoice.objects.filter(
        user=request.user, 
        status='unpaid'
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    total_clients = Client.objects.filter(user=request.user).count()
    
    # Recent invoices
    recent_invoices = Invoice.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Monthly revenue data for chart (last 6 months)
    monthly_data = []
    for i in range(6):
        month_start = (timezone.now() - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        monthly_revenue = Invoice.objects.filter(
            user=request.user,
            status='paid',
            date_issued__range=[month_start, month_end]
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': float(monthly_revenue)
        })
    
    monthly_data.reverse()
    
    context = {
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'unpaid_invoices': unpaid_invoices,
        'overdue_invoices': overdue_invoices,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'total_clients': total_clients,
        'recent_invoices': recent_invoices,
        'monthly_data': monthly_data,
    }
    
    return render(request, 'users/dashboard.html', context)

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'users/profile.html', {'form': form})
