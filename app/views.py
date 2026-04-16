from urllib import request, response

from django.conf import settings
from django.contrib import messages
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views import View
from .forms import CustomerRegistrationForm, CustomerProfileForm, ReviewForm
from .models import Product, Customer, Cart, Order, Review, Wishlist, Payment, OrderItem
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
from django.contrib.auth.views import LogoutView
from django.contrib import messages
from django.views.generic import UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from app.payments.montonio import create_montonio_payment
import jwt
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.html import strip_tags

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
        
        reviews = product.reviews.all()
        
        # Empty form for review submission
        form = ReviewForm()

        return render(request, "app/productdetail.html", {
            "product": product,
            "wishlist": wishlist,
            "reviews": reviews,
            "form": form,
        })

    def post(self, request, pk):
        """Handle review submission."""
        if not request.user.is_authenticated:            
            return JsonResponse({'error': 'Authentication required'}, status=403)

        product = get_object_or_404(Product, pk=pk)

        # Check if user already has a review
        if Review.objects.filter(product=product, user=request.user).exists():
            return JsonResponse({'error': 'You can only submit one review per product.'}, status=400)
    
        form = ReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()

             # SEND NOTIFICATION TO MICROSERVICE
            send_review_notification(review)

            return JsonResponse({
                    'success': True,
                    'rating': review.rating,
                    'comment': review.comment,
                    'product_rating': product.average_rating(),
                    'review_count': product.reviews.count()
                })

        return JsonResponse({'error': 'Invalid form'}, status=400)
    
def send_review_notification(review):
    """Send review notification to microservice."""
    try:
        payload = {           
            "product_name": review.product.title,           
            "username": review.user.username,
            "rating": review.rating,
            "comment": review.comment,
        }

        # URL of review notification microservice
        url = "http://localhost:8002/notify/review/"

        response = requests.post(url, json=payload, timeout=8)

        print("MICROSERVICE STATUS:", response.status_code)
        print("MICROSERVICE RESPONSE:", response.text)        

    except Exception as e:
        print("Notification microservice error:", e)
    
class ReviewUpdateView(UpdateView):
    model = Review
    form_class = ReviewForm

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        form = ReviewForm(request.POST, instance=self.object)
        
        if form.is_valid():
            form.save()
            product = self.object.product

            return JsonResponse({
                'success': True,
                'rating': self.object.rating,
                'comment': self.object.comment,
                'product_rating': product.average_rating(),
                'review_count': product.reviews.count()
            })
        
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

class ReviewDeleteView(DeleteView):
    model = Review

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        product = self.object.product
        self.object.delete()

        return JsonResponse({
            'success': True,
            'product_rating': product.average_rating(),
            'review_count': product.reviews.count()
        })

class CustomerRegistrationView(View):
    def get(self, request):
        form = CustomerRegistrationForm()
        return render(request, 'app/customerregistration.html', {'form': form})

    def post(self, request):
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Token 
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            activation_link = request.build_absolute_uri(
                reverse('activate', kwargs={'uidb64': uid, 'token': token})
            )

            # E-mail for verification
            html_message = render_to_string('app/email_activation.html', {
                'username': user.username,
                'activation_link': activation_link,
            })

            plain_message = strip_tags(html_message)

            send_mail(
                subject='Activate your AgroShop account',
                message=plain_message,
                from_email='noreply@yourshop.com',
                recipient_list=[user.email],
                html_message=html_message,
            )

            messages.success(request, 'Please check your email to activate your account.')  # save the new user 
           
            form = CustomerRegistrationForm()

        else:
            messages.warning(request, 'Invalid Input Data')
        return render(request, 'app/customerregistration.html', {'form': form})
    
def activate_account(request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except Exception:
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_active = True

            # Send notification to the microservice
            try:
                requests.post(
                    "http://127.0.0.1:8001/send-user-registered/",
                    json={
                        "username": user.username,
                        "email": user.email
                    },
                    timeout=5
                )
            except Exception as e:
                print("Microservice error:", e)

            user.save()
            
            return render(request, 'app/activation_success.html')
        else:
            return HttpResponse("Activation link is invalid!")
    
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
            messages.success(request, 'A New Address Added Successfully')
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

def calculate_cart_totals(user):
    cart = Cart.objects.filter(user=user)

    amount = Decimal('0.0')
    for item in cart:
        amount += item.quantity * item.product.discounted_price

    shipping_amount = Decimal('5.00') if cart.exists() else Decimal('0.0')
    total_amount = amount + shipping_amount

    return amount, shipping_amount, total_amount  

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
        return JsonResponse({'success': True, 'cart_count': cart_count})
    
    # If normal form (Buy Now) - redirect to cart page
    return redirect('showcart')

def show_cart(request):
    user = request.user
    cart = Cart.objects.filter(user=user)

    amount, shipping_amount, total_amount = calculate_cart_totals(user)

    context = {
        'cart': cart,
        'amount': amount,
        'shipping_amount': shipping_amount,
        'total_amount': total_amount,
    }

    return render(request, 'app/addtocart.html', context)

def plus_cart(request):
    if request.method == "GET":
        prod_id = request.GET.get('prod_id')
        user = request.user

        cart_item = Cart.objects.get(user=user, product_id=prod_id)
        cart_item.quantity += 1
        cart_item.save()

        # totals
        amount, shipping_amount, total_amount = calculate_cart_totals(user)

        item_total = cart_item.quantity * cart_item.product.discounted_price

        return JsonResponse({
            'quantity': cart_item.quantity,
            'product_id': cart_item.product.id,
            'item_total': float(item_total),
            'amount': float(amount),
            'totalamount': float(total_amount),
        })
        
def minus_cart(request):
    if request.method == "GET":
        prod_id = request.GET.get('prod_id')
        user = request.user

        cart_item = Cart.objects.get(user=user, product_id=prod_id)
        cart_item.quantity -= 1

        if cart_item.quantity <= 0:
            cart_item.delete()
            quantity = 0
            item_total = 0
        else:
            cart_item.save()
            quantity = cart_item.quantity
            item_total = quantity * cart_item.product.discounted_price

        # totals
        amount, shipping_amount, total_amount = calculate_cart_totals(user)

        return JsonResponse({
            'quantity': quantity,
            'product_id': int(prod_id),
            'item_total': float(item_total),
            'amount': float(amount),
            'totalamount': float(total_amount),
        })
    
class checkout(View):
    def get(self, request):
        user = request.user
        add = Customer.objects.filter(user=user)
        cart_items = Cart.objects.filter(user=user)

        amount = Decimal('0.0')
        shippingamount = Decimal('5.00')

        if cart_items.exists():
            for item in cart_items:
                amount += item.quantity * item.product.discounted_price

        totalamount = amount + shippingamount

        has_address = add.exists()

        return render(request, 'app/checkout.html', {
            'add': add,
            'cart_items': cart_items,
            'amount': amount,
            'shippingamount': shippingamount,
            'totalamount': totalamount,
            'has_address': has_address,
        })

def orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-ordered_date')

    status_progress = {
        'Pending': 10,
        'Accepted': 25,
        'Packed': 50,
        'On The Way': 75,
        'Delivered': 100,
        'Cancelled': 100,
    }

    status_color = {
        'Pending': 'secondary',
        'Accepted': 'info',
        'Packed': 'primary',
        'On The Way': 'warning',
        'Delivered': 'success',
        'Cancelled': 'danger',
    }

    for order in orders:
        order.progress = status_progress.get(order.status, 0)
        order.color = status_color.get(order.status, 'secondary')
    
    return render(request, 'app/orders.html', {'orders': orders})

class CreateOrderView(View):
    def post(self, request, *args, **kwargs):

        custid = request.POST.get("custid")

        if not custid:
            return JsonResponse({"error": "Select address"}, status=400)

        cart_items = Cart.objects.filter(user=request.user)

        if not cart_items.exists():
            return JsonResponse({"error": "Cart empty"}, status=400)

        shipping = Decimal("5.00")

        total = sum(
            Decimal(item.quantity) * Decimal(item.product.discounted_price)
            for item in cart_items
        ) + shipping

        customer = Customer.objects.get(id=custid)

        # 1. Create Payment (pending)
        payment = Payment.objects.create(
            user=request.user,
            amount=total,
            paid=False
        )

        # 2. Create Order (pending)
        order = Order.objects.create(
            user=request.user,
            customer=customer,
            total_amount=total,
            payment=payment,
            status="Pending"
        )

        # 3. Order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity
            )

        # 4. Montonio payment session
        response = create_montonio_payment(order)

        if response.get("uuid"):
            payment.transaction_id = response.get("uuid")
            payment.status = response.get("paymentStatus")
            payment.provider = "montonio"
            payment.save()

        payment_url = response.get("paymentUrl")

        if not payment_url:
            print("Montonio error:", response)
            return JsonResponse({"error": "Payment creation failed"}, status=500)

        return redirect(payment_url)

@csrf_exempt
def montonio_webhook(request):
    try:
        data = json.loads(request.body)
        token = data.get("orderToken")

        if not token:
            return JsonResponse({"error": "No token"}, status=400)

        decoded = jwt.decode(
            token,
            settings.MONTONIO_SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_iat": False}
        )

        if decoded.get("paymentStatus") == "PAID":
            order_id = decoded.get("merchantReference")

            order = Order.objects.get(id=order_id)           

            if order.payment:
                order.payment.status = "PAID"
                order.payment.paid = True
                order.payment.save()

            order.save()

            # iztīra cart
            Cart.objects.filter(user=order.user).delete()

        return JsonResponse({"ok": True})

    except Exception as e:
        print("Webhook error:", e)
        return JsonResponse({"error": "Webhook failed"}, status=500)
    
def payment_success(request):
    token = request.GET.get("order-token")

    if not token:
        return HttpResponse("Missing order token", status=400)

    try:
        decoded = jwt.decode(
            token,
            settings.MONTONIO_SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_iat": False}
        )

        order_id = decoded.get("merchantReference")

        order = Order.objects.get(id=order_id)
        
        if request.user.is_authenticated and order.user != request.user:
            return HttpResponse("Unauthorized", status=403)

        return render(request, "app/payment_success.html", {
            "order": order
        })

    except Exception as e:
        print("Payment success error:", e)
        return HttpResponse("Something went wrong", status=500)

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

        cart_count = cart_products.count()

        data = {
            'quantity': 0,  # removed, so quantity is 0
            'amount': float(amount),
            'totalamount': float(amount + shippingamount),
            'cart_count': cart_count,
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

class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        # First call original logout logic
        response = super().dispatch(request, *args, **kwargs)

        # Clear all queued messages AFTER logout
        list(messages.get_messages(request))

        return response