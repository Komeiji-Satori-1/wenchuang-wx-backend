from django.http import JsonResponse
from django.shortcuts import render,HttpResponse,get_object_or_404
from admin_panel.decorators import admin_login_required
from .models import Product,Category,ProductLog,AdminUser
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.
@admin_login_required
def product_home(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request,'product_home.html',{'products':products,'categories':categories})

def add_product(request):
    if request.method == "POST":
        name = request.POST['name']
        price = request.POST['price']
        category_id = request.POST['category']
        stock = request.POST['stock']
        description = request.POST['description']

        try:
            category = Category.objects.get(id=category_id)
            product = Product.objects.create(

                name=name,
                price=price,
                category=category,
                stock=stock,
                description=description,

                )
            ProductLog.objects.create(
                product=product,
                action='create',
                old_value='',
                new_value=f'产品 {product.name} 创建成功',
                change_amount=product.stock,
                admin_id=request.session.get('admin_user_id'),
            )

            return JsonResponse({'success':True,"id": product.id})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "无效请求"})

@admin_login_required
def product_detail(request):
    product_id = request.GET.get("productId")
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'product_detail.html', {'product': product})

@csrf_exempt
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({"success": False, "error": "产品不存在"})
        old_stock = product.stock
        old_data = {
            "name": product.name,
            "price": str(product.price),
            "stock": product.stock,
            "category": str(product.category) if product.category else None
        }
        product.name = request.POST.get("name", product.name)
        product.price = request.POST.get("price", product.price)
        product.stock = request.POST.get("stock", product.stock)
        product.category = request.POST.get('category', product.category)

        change_amount = int(product.stock) - int(old_stock)

        product.save()

        action=request.POST.get("action_choice", "None"),
        ProductLog.objects.create(
            product=product,
            action=action,
            old_value=old_data,
            new_value=f"{product.name}, {product.price}, {product.stock}",
            change_amount=change_amount,
            admin_id=request.session.get('admin_user_id'),
        )
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid request method"})

@csrf_exempt
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        old_data = f"{product.name}, {product.price}, {product.stock}"
        product.delete()

        ProductLog.objects.create(
            product_id=product_id,
            action='delete',
            old_value=old_data,
            new_value='已删除',
            change_amount=0,
            admin_id=request.session.get('admin_user_id'),
        )
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid request method"})

def product_log(request):
    logs = ProductLog.objects.select_related("product", "admin").all().order_by("-created_at")
    return render(request, "product_log.html", {"logs": logs})
