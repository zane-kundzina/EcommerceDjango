from .models import Cart, Wishlist

def cart_item_count(request):
    if request.user.is_authenticated:
        return {'cart_item_count': Cart.objects.filter(user=request.user).count()}
    return {'cart_item_count': 0}

def wishlist_item_count(request):
    count = 0
    if request.user.is_authenticated:
        count = Wishlist.objects.filter(user=request.user).count()
    return {
        'wishlist_count': count
    }
