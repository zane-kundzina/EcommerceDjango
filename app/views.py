from django.contrib import messages
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views import View
from .models import Product
from .forms import CustomerRegistrationForm, CustomerProfileForm
from .models import Customer, Cart, Order, Wishlist
from decimal import Decimal
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin


# Create your views here.
def home (request):
    return render(request, "app/home.html")

def aboutus (request):
    return render(request, "app/aboutus.html")

def contact (request):
    return render(request, "app/contact.html")

class CategoryView(View):
    def get(self, request, val):  
        product = Product.objects.filter(category=val)
        title = Product.objects.filter(category=val).values('title')
        return render(request, "app/category.html", locals())
    
class CategoryTitleView(View):
    def get(self, request, val):  
        product = Product.objects.filter(title=val)
        title = Product.objects.filter(category=product[0].category).values('title')
        return render(request, "app/category.html", locals())

class ProductDetailView(View):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        
        # Only check wishlist if user is authenticated
        wishlist = None
        if request.user.is_authenticated:
            wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
        
        return render(request, "app/productdetail.html", {"product": product, "wishlist": wishlist}) 
    

class CustomerRegistrationView(View):
    def get(self, request):
        form = CustomerRegistrationForm()
        return render(request, 'app/customerregistration.html', {'form': form})

    def post(self, request):
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()            
            messages.success(request, 'User Registered Successfully')
            form = CustomerRegistrationForm()
        else:
            messages.warning(request, 'Invalid Input Data')
        return render(request, 'app/customerregistration.html', {'form': form})
    
class ProfileView(View):
    def get(self, request):
        form = CustomerProfileForm()
        add = Customer.objects.filter(user=request.user)
        return render(request, 'app/profile.html', {'form': form, 'add': add})
    
    def post(self, request):
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            reg = form.save(commit=False)
            reg.user = request.user
            reg.save()
            messages.success(request, 'Profile Updated Successfully')
            form = CustomerProfileForm()
        else:
            messages.warning(request, 'Invalid Input Data')
        return render(request, 'app/profile.html', locals())
    
def address(request):
    add = Customer.objects.filter(user=request.user)
    return render(request, 'app/address.html', {'add': add})

class UpdateAddressView(View):
    def get(self, request, pk):
        add = Customer.objects.get(pk=pk)
        form = CustomerProfileForm(instance=add)
        return render(request, 'app/updateaddress.html', {'form': form})
    
    def post(self, request, pk):
        add = Customer.objects.get(pk=pk)
        form = CustomerProfileForm(request.POST, instance=add)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address Updated Successfully')
        else:
            messages.warning(request, 'Invalid Input Data')
        return redirect('address')
    
def delete_address(request, pk):
    add = Customer.objects.get(pk=pk)
    add.delete()
    messages.success(request, 'Address Deleted Successfully')
    return redirect('address')
    
def add_to_cart(request):
    user=request.user
    pk=request.POST.get('product_id')
    product=Product.objects.get(pk=pk)
    existing_cart_item = Cart.objects.filter(user=user, product=product).first()
    if existing_cart_item:
        # If product already in cart, increase quantity
        existing_cart_item.quantity += 1
        existing_cart_item.save()
    else:
        # Otherwise, create a new cart entry
        Cart.objects.create(user=user, product=product, quantity=1)    
    return redirect('/cart')

def show_cart(request):
    user = request.user
    cart = Cart.objects.filter(user=user)
    amount = Decimal('0.0')
    shippingamount = Decimal('5.00')
    totalamount = Decimal('0.0')

    cart_product = [p for p in Cart.objects.all() if p.user == user]

    if cart_product:
            for p in cart_product:
                tempamount = (p.quantity * p.product.discounted_price)
                amount += tempamount
            totalamount = amount + shippingamount

            context = {
            'cart': cart,
            'amount': amount,
            'shippingamount': shippingamount,
            'totalamount': totalamount,
            }

            return render(request, 'app/addtocart.html', context)
    else:
            return render(request, 'app/emptycart.html')
    
class checkout(View):
    def get(self, request):
        user = request.user
        add = Customer.objects.filter(user=user)
        cart_items = Cart.objects.filter(user=user)
        amount = Decimal('0.0')
        shippingamount = Decimal('5.00')
        totalamount = Decimal('0.0')

        cart_product = [p for p in Cart.objects.all() if p.user == user]

        if cart_product:
            for p in cart_product:
                tempamount = (p.quantity * p.product.discounted_price)
                amount += tempamount
            totalamount = amount + shippingamount

        return render(request, 'app/checkout.html', locals()) 

def orders(request):
    op = Order.objects.filter(user=request.user)
    return render(request, 'app/orders.html', {'order_placed': op})


def payment_done(request):
    user = request.user
    custid = request.GET.get('custid')
    customer = Customer.objects.get(id=custid)
    cart = Cart.objects.filter(user=user)
    for c in cart:
        Order.objects.create(user=user, customer=customer, product=c.product, quantity=c.quantity)
        c.delete()
    return redirect("orders")


def plus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET.get('prod_id')
        try:
            c = Cart.objects.get(product__id=prod_id, user=request.user)
            c.quantity += 1
            c.save()
        except Cart.DoesNotExist:
            return JsonResponse({'error': 'Cart item not found'}, status=404)

        amount = Decimal('0.0')
        shippingamount = Decimal('5.0')
        cart_product = Cart.objects.filter(user=request.user)

        for p in cart_product:
            tempamount = p.quantity * p.product.discounted_price
            amount += tempamount

        data = {
            'quantity': c.quantity,
            'amount': str(amount),  # Convert Decimal to string for JSON
            'totalamount': str(amount + shippingamount)
        }
        return JsonResponse(data)

def minus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET['prod_id']
        c = Cart.objects.filter(product__id=prod_id, user=request.user).first()

        # Decrease quantity, but not below 1
        if c.quantity > 1:
            c.quantity -= 1
            c.save()
        else:
            c.delete()  # remove item completely if quantity becomes 0

        amount = Decimal('0.0')
        shippingamount = Decimal('5.0')
        cart_product = [p for p in Cart.objects.all() if p.user == request.user]

        for p in cart_product:
            tempamount = p.quantity * p.product.discounted_price
            amount += tempamount

        data = {
            'quantity': c.quantity if c.id else 0,
            'amount': float(amount),
            'totalamount': float(amount + shippingamount)
        }
        return JsonResponse(data)

def remove_cart(request):
    if request.method == 'GET':
        prod_id = request.GET['prod_id']
        c = Cart.objects.filter(product__id=prod_id, user=request.user).first()

        if c:
            c.delete()  # remove the item completely

        amount = Decimal('0.0')
        shippingamount = Decimal('5.0')
        cart_products = Cart.objects.filter(user=request.user)

        for p in cart_products:
            tempamount = p.quantity * p.product.discounted_price
            amount += tempamount

        data = {
            'quantity': 0,  # removed, so quantity is 0
            'amount': float(amount),
            'totalamount': float(amount + shippingamount)
        }
        return JsonResponse(data)

@login_required  
def plus_wishlist(request):
    if request.method == 'GET':
        prod_id = request.GET.get('prod_id')
        product = Product.objects.get(id=prod_id)
        user = request.user if request.user.is_authenticated else None

        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if created:
            action = 'added'
        else:
            action = 'exists'

        data = {
            'action': action
        }
        return JsonResponse(data)
@login_required
def minus_wishlist(request):
    if request.method == 'GET':
        prod_id = request.GET['prod_id']
        user = request.user if request.user.is_authenticated else None
        wishlist_item = Wishlist.objects.filter(product__id=prod_id, user=request.user).first()

        if wishlist_item:
            wishlist_item.delete()  # remove the item completely
            action = 'removed'
        else:
            action = 'not_found'

        data = {
            'action': action
        }
        return JsonResponse(data)
    
def search(request):
    query = request.GET.get('search')
    totalitem=0
    wishitem=0
    if request.user.is_authenticated:
        totalitem = Cart.objects.filter(user=request.user).count()
        wishitem = Wishlist.objects.filter(user=request.user).count()
    product = Product.objects.filter(
        Q(title__icontains=query) | Q(category__icontains=query) | Q(description__icontains=query)
    )
    return render(request, 'app/search.html', {'product': product})