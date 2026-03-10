from .models import Product

def product_list(request):
    return {
        "product_list": Product.objects.all()
    }