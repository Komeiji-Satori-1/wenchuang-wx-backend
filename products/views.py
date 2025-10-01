from django.http import JsonResponse
from django.shortcuts import render,HttpResponse,get_object_or_404
from admin_panel.decorators import admin_login_required
from .models import Product,Category

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

            return JsonResponse({'success':True,"id": product.id})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "无效请求"})

@admin_login_required
def product_detail(request):
    product_id = request.GET.get("productId")
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'product_detail.html', {'product': product})