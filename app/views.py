from django.conf import settings
from django.contrib import messages
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views import View
from .models import Product
from .forms import CustomerRegistrationForm, CustomerProfileForm
from .models import Customer, Cart, Order, Wishlist, Payment, OrderItem
from decimal import Decimal
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
from .paypal_client import PayPalClient
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import requests
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment


logger = logging.getLogger(__name__)
paypal_client = PayPalClient()

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
    
    cart_count = Cart.objects.filter(user=user).count()

    # If AJAX request - return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'cart_count': cart_count})

    # If normal form (Buy Now) - redirect to cart page
    return redirect('showcart')

def show_cart(request):
    user = request.user
    cart = Cart.objects.filter(user=user)

    amount = Decimal('0.0')
    shipping_amount = Decimal('5.00')
    total_amount = Decimal('0.0')

    if cart.exists():
        # Calculate total for cart items
        for item in cart:
            amount += item.quantity * item.product.discounted_price
        total_amount = amount + shipping_amount
    else:
        total_amount = 0
        shipping_amount = 0  

    # Create PayPal order
    paypal_client = PayPalClient()
    request_order = OrdersCreateRequest()
    request_order.prefer('return=representation')
    request_order.request_body({
        "intent": "CAPTURE",
        "purchase_units": [
            {"amount": {"currency_code": "EUR", "value": f"{total_amount:.2f}"}}
        ],
        "application_context": {"shipping_preference": "NO_SHIPPING"}
    })
    response = paypal_client.client.execute(request_order)

    order_id = response.result.id

    context = {
        'cart': cart,
        'amount': amount,
        'shipping_amount': shipping_amount,
        'total_amount': total_amount,
        'paypal_order_id': order_id,  # Pass pre-created order ID to template
    }

    return render(request, 'app/addtocart.html', context)
    
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

        paypal_client_id = settings.PAYPAL_CLIENT_ID

        return render(request, 'app/checkout.html', {
            'add': add,
            'cart_items': cart_items,
            'amount': amount,
            'shippingamount': shippingamount,
            'totalamount': totalamount,
            'paypal_client_id': paypal_client_id
        }) 

def orders(request):
    op = Order.objects.filter(user=request.user)
    return render(request, 'app/orders.html', {'order_placed': op})

class CreateOrderView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User not authenticated'}, status=403)

        # Get all cart items for this user
        cart_items = Cart.objects.filter(user=request.user)

        if not cart_items.exists():
            return JsonResponse({'error': 'Your cart is empty.'}, status=400)

        # Calculate total cost including shipping
        shipping_amount = Decimal('5.00')
        total_amount = sum(
            Decimal(item.quantity) * Decimal(item.product.discounted_price)
            for item in cart_items
        ) + shipping_amount

        total_amount_str = f"{total_amount:.2f}"  # PayPal requires string

        try:
            # Create PayPal order request
            request_data = OrdersCreateRequest()
            request_data.prefer('return=representation')
            request_data.request_body({
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "amount": {
                            "currency_code": "EUR",
                            "value": total_amount_str
                        },
                        "description": f"Order by {request.user.username}"
                    }
                ],
                "application_context": {
                    "shipping_preference": "NO_SHIPPING"
                }
            })

            # Execute request using the paypal_client instance
            response = paypal_client.client.execute(request_data)

            # Save Payment object
            payment = Payment.objects.create(
                user=request.user,
                amount=total_amount,
                paypal_order_id=response.result.id,
                paid=False
            )

            customer = Customer.objects.get(user=request.user)

            # Create the Order
            order = Order.objects.create(
                user=request.user,
                customer=customer,
                total_amount=total_amount,
                payment=payment,  # the Payment object you just created
                paypal_order_id=response.result.id
            )

            # Create OrderItems for each cart item
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity
                )

            # Optional: clear cart after creating the order
            cart_items.delete()

            # Return PayPal order ID
            return JsonResponse({'id': response.result.id})

        except Exception as e:
            logger.exception("PayPal order creation failed")
            return JsonResponse({'error': 'Failed to create PayPal order.'}, status=500)
        
        



@csrf_exempt
def create_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        custid = data.get('custid')
        if not custid:
            return JsonResponse({'error': 'Please select a shipping address!'}, status=400)

        # Fetch all cart items for this user
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return JsonResponse({'error': 'Your cart is empty!'}, status=400)

        # Calculate total amount
        total_amount = sum([item.quantity * item.product.discounted_price for item in cart_items])
        total_amount = round(total_amount, 2)  # PayPal prefers 2 decimals

        # Create a PayPal order
        request_order = OrdersCreateRequest()
        request_order.prefer('return=representation')
        request_order.request_body({
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": "EUR",
                    "value": str(total_amount)
                }
            }]
        })

        client = PayPalClient().client
        response = client.execute(request_order)

        # Save a Payment record in your DB with pending status
        Payment.objects.create(
            user=request.user,
            customer_id=custid,
            total_amount=total_amount,
            paypal_order_id=response.result.id,
            paid=False
        )

        # Return the PayPal order ID to JS
        return JsonResponse({'id': response.result.id})

    return JsonResponse({'error': 'Invalid request'}, status=400)

class CaptureOrderView(PayPalClient):
    def post(self, request, order_id, *args, **kwargs):
        request_capture = OrdersCaptureRequest(order_id)
        request_capture.request_body({})
        response = self.client.client.execute(request_capture)
        return JsonResponse(response.result.__dict__)

class CapturePaymentView(PayPalClient, View):
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            order_id = data.get('orderID')
            custid = data.get('custid')

            if not order_id or not custid:
                return JsonResponse({'status': 'error', 'error': 'Missing order ID or customer ID'}, status=400)

            # Capture the payment using PayPal SDK
            capture_request = OrdersCaptureRequest(order_id)
            capture_request.request_body({})
            response = self.client.client.execute(capture_request)

            if response.result.status != "COMPLETED":
                return JsonResponse({'status': 'error', 'error': 'Payment not completed on PayPal'}, status=400)

            # Retrieve or create Payment record
            payment = Payment.objects.filter(paypal_order_id=order_id).first()
            if not payment:
                payment = Payment.objects.create(
                    user=request.user,
                    amount=Decimal(response.result.purchase_units[0].amount.value),
                    paypal_order_id=order_id
                )

            # Update payment status
            payment.paid = True
            payment.paypal_payment_id = response.result.purchase_units[0].payments.captures[0].id
            payment.payer_email = response.result.payer.email_address
            payment.paypal_status = response.result.status
            payment.save()

            # Create order and order items
            customer = Customer.objects.get(id=custid)
            cart_items = Cart.objects.filter(user=request.user)

            if not cart_items.exists():
                return JsonResponse({'status': 'error', 'error': 'Cart is empty'}, status=400)

            # Calculate total
            shipping_amount = Decimal('5.00')
            total_amount = sum(
                Decimal(item.quantity) * Decimal(item.product.discounted_price)
                for item in cart_items
            ) + shipping_amount

            # Create Order entry
            order = Order.objects.create(
                user=request.user,
                customer=customer,
                payment=payment,
                total_amount=total_amount
            )

            # Create OrderItem entries
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity
                )

            # Clear the user's cart
            cart_items.delete()

            return JsonResponse({'status': 'success'})

        except Exception as e:
            print(f"Error capturing payment: {e}")
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

@csrf_exempt
def capture_payment(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        order_id = data.get('orderID')
        custid = data.get('custid')

        # Capture payment using PayPal SDK
        from paypalcheckoutsdk.orders import OrdersCaptureRequest
        request_capture = OrdersCaptureRequest(order_id)
        request_capture.prefer('return=representation')

        client = PayPalClient().client
        response = client.execute(request_capture)

        if response.result.status == "COMPLETED":
            # Save Payment
            payment = Payment.objects.get(paypal_order_id=order_id)
            payment.paid = True
            payment.paypal_payment_id = response.result.purchase_units[0].payments.captures[0].id
            payment.payer_email = response.result.payer.email_address
            payment.paypal_status = response.result.status
            payment.save()

            # Create Orders for each cart item
            cart_items = Cart.objects.filter(user=request.user)
            customer = Customer.objects.get(id=custid)
            for item in cart_items:
                Order.objects.create(
                    user=request.user,
                    customer=customer,
                    product=item.product,
                    quantity=item.quantity,
                    payment=payment,
                    paypal_order_id=order_id
                )
            # Clear the cart
            cart_items.delete()

            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'error': 'Payment not completed'})

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
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    totalitem = Cart.objects.filter(user=request.user).count()
    wishlist_count = wishlist_items.count()

    context = {
        'wishlist_items': wishlist_items,
        'cart_item_count': totalitem,
        'wishlist_count': wishlist_count,
    }

    return render(request, 'app/wishlist.html', context)

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