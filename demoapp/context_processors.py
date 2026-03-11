from .models import Product
from .models import Favorite
from decimal import Decimal

def product_list(request):
    return {
        "product_list": Product.objects.all()
    }

def favorite_count(request):

    count = 0

    if request.user.is_authenticated:
        count = Favorite.objects.filter(user=request.user).count()

    return {
        "favorite_count": count
    }    
def cart_total(request):

    cart = request.session.get('cart', {})

    subtotal = 0
    cart_count = 0

    for item in cart.values():
        subtotal += Decimal(item['price']) * item['quantity']
        cart_count += item['quantity']

    return {
        "subtotal": subtotal,
        "cart_count": cart_count
    }

