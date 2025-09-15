from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import ProductService
from .product_service_forms import ProductServiceForm

@login_required
def product_service_list_view(request):
    products = ProductService.objects.filter(user=request.user, is_active=True)
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
    }
    return render(request, 'invoices/product_service_list.html', context)

@login_required
def product_service_create_view(request):
    if request.method == 'POST':
        form = ProductServiceForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()
            messages.success(request, f'Product/Service "{product.name}" created successfully!')
            return redirect('product_service_list')
    else:
        form = ProductServiceForm()
    
    context = {
        'form': form,
        'title': 'Add New Product/Service',
    }
    return render(request, 'invoices/product_service_form.html', context)

@login_required
def product_service_update_view(request, pk):
    product = get_object_or_404(ProductService, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ProductServiceForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product/Service "{product.name}" updated successfully!')
            return redirect('product_service_list')
    else:
        form = ProductServiceForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'title': f'Edit Product/Service',
    }
    return render(request, 'invoices/product_service_form.html', context)

@login_required
def product_service_delete_view(request, pk):
    product = get_object_or_404(ProductService, pk=pk, user=request.user)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product/Service "{product_name}" deleted successfully!')
        return redirect('product_service_list')
    
    context = {
        'product': product,
    }
    return render(request, 'invoices/product_service_confirm_delete.html', context)

@login_required
def product_service_lookup_view(request):
    """
    API endpoint for looking up products/services for invoice items
    """
    if request.method == 'GET':
        query = request.GET.get('q', '')
        products = ProductService.objects.filter(
            user=request.user,
            is_active=True
        )
        
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )
        
        # Return JSON response with product data
        data = [
            {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'unit_price': float(product.unit_price),
            }
            for product in products[:10]  # Limit to 10 results
        ]
        
        return JsonResponse({'products': data})