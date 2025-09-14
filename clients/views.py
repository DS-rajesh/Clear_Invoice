from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Client
from .forms import ClientForm, ClientSearchForm

@login_required
def client_list_view(request):
    form = ClientSearchForm(request.GET)
    clients = Client.objects.filter(user=request.user)
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        is_active = form.cleaned_data.get('is_active')
        
        if search:
            clients = clients.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(company__icontains=search)
            )
        
        if is_active:
            clients = clients.filter(is_active=is_active == 'true')
    
    paginator = Paginator(clients, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'clients': page_obj,
    }
    return render(request, 'clients/client_list.html', context)

@login_required
def client_detail_view(request, pk):
    client = get_object_or_404(Client, pk=pk, user=request.user)
    invoices = client.invoices.all()[:5]  # Recent invoices
    
    context = {
        'client': client,
        'invoices': invoices,
    }
    return render(request, 'clients/client_detail.html', context)

@login_required
def client_create_view(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.user = request.user
            client.save()
            messages.success(request, f'Client "{client.name}" created successfully!')
            return redirect('client_detail', pk=client.pk)
    else:
        form = ClientForm()
    
    context = {
        'form': form,
        'title': 'Add New Client',
    }
    return render(request, 'clients/client_form.html', context)

@login_required
def client_update_view(request, pk):
    client = get_object_or_404(Client, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f'Client "{client.name}" updated successfully!')
            return redirect('client_detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)
    
    context = {
        'form': form,
        'client': client,
        'title': f'Edit {client.name}',
    }
    return render(request, 'clients/client_form.html', context)

@login_required
def client_delete_view(request, pk):
    client = get_object_or_404(Client, pk=pk, user=request.user)
    
    if request.method == 'POST':
        client_name = client.name
        client.delete()
        messages.success(request, f'Client "{client_name}" deleted successfully!')
        return redirect('client_list')
    
    context = {
        'client': client,
    }
    return render(request, 'clients/client_confirm_delete.html', context)
