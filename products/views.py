from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from admin_panel.decorators import admin_login_required
from .models import Product, Category, ProductLog,AdminUser
from django.views.decorators.csrf import csrf_exempt
import json


# ------------------ 产品主页 ------------------
@admin_login_required
def product_home(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, 'product_home.html', {'products': products, 'categories': categories})

def product_search(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, 'product_home.html', {'products': products, 'categories': categories})


# ------------------ 添加产品 ------------------
@csrf_exempt
def add_product(request):
    if request.method == "POST":
        name = request.POST['name']
        price = request.POST['price']
        category_id = request.POST['category']
        stock = request.POST['stock']
        description = request.POST['description']
        image = request.FILES.get('image')

        try:
            category = Category.objects.get(id=category_id)
            product = Product.objects.create(
                name=name,
                price=price,
                category=category,
                stock=stock,
                description=description,
                image=image,
            )
            new_data = {
                "name": product.name,
                "price": str(product.price),
                "stock": product.stock,
                "category": str(product.category) if product.category else None,
            }
            ProductLog.objects.create(
                product=product,
                action="create",
                old_value={},
                new_value=json.dumps(new_data,ensure_ascii=False),
                change_amount=int(stock),
                admin_id=request.session.get('admin_user_id'),
            )

            return JsonResponse({'success': True, "id": product.id})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "无效请求"})


# ------------------ 产品详情 ------------------
@admin_login_required
def product_detail(request):
    product_id = request.GET.get("productId")
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'product_detail.html', {'product': product})


# ------------------ 编辑产品 ------------------
@csrf_exempt
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        old_stock = product.stock
        old_data = {
            "name": product.name,
            "price": str(product.price),
            "stock": product.stock,
            "category": str(product.category) if product.category else None,
        }

        product.name = request.POST.get("name", product.name)
        product.price = request.POST.get("price", product.price)
        product.stock = int(request.POST.get("stock", product.stock))
        product.category_id = request.POST.get("category", product.category_id)

        if 'image' in request.FILES:
            product.image = request.FILES['image']

        product.save()

        change_amount = product.stock - old_stock
        action = request.POST.get("action_choice", "update")
        new_data = {
            "name": product.name,
            "price": str(product.price),
            "stock": product.stock,
            "category": str(product.category) if product.category else None,
            }

        ProductLog.objects.create(
            product=product,
            action=action,
            old_value=json.dumps(old_data, ensure_ascii=False),
            new_value=json.dumps(new_data, ensure_ascii=False),
            change_amount=change_amount,
            admin_id=request.session.get('admin_user_id'),
        )

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request method"})


# ------------------ 删除产品 ------------------
@csrf_exempt
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        old_data = {
            "name": product.name,
            "price": str(product.price),
            "stock": product.stock,
        }

        # ✅ 删除前记录日志，防止外键约束报错
        ProductLog.objects.create(
            product=product,
            action="delete",
            old_value=old_data,
            new_value={"status": "已删除"},
            change_amount=0,
            admin_id=request.session.get('admin_user_id'),
        )

        product.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request method"})


# ------------------ 操作日志页面 ------------------
@admin_login_required
def product_log(request):
    logs = ProductLog.objects.select_related("product", "admin").order_by("-created_at")

    formatted_logs = []
    for entry in logs:
        # 尝试将 JSON 字符串转换为字典，避免模板里显示原始 JSON 文本
        try:
            old_val = json.loads(entry.old_value) if entry.old_value else {}
        except json.JSONDecodeError:
            old_val = entry.old_value or {}

        try:
            new_val = json.loads(entry.new_value) if entry.new_value else {}
        except json.JSONDecodeError:
            new_val = entry.new_value or {}

        formatted_logs.append({
            "product_name": entry.product.name if entry.product else "（已删除）",
            "action": entry.action,
            "old_value": old_val,
            "new_value": new_val,
            "change_amount": entry.change_amount,
            "admin": entry.admin.username if entry.admin else "系统",
            "created_at": entry.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return render(request, "product_log.html", {"logs": formatted_logs})
