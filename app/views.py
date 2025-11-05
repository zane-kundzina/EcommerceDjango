from django.contrib import messages
from django.db.models import Count
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import View
from .models import Product
from .forms import CustomerRegistrationForm, CustomerProfileForm
from .models import Customer, Cart
from decimal import Decimal

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
        product = Product.objects.get(pk=pk)
        return render(request, "app/productdetail.html", locals())   
    

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