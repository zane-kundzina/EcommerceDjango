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
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import requests
from django.utils.decorators import method_decorator
import logging
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
from .notifications import handle_event
from asgiref.sync import async_to_sync
import datetime
from django.shortcuts import redirect
from django.db import transaction

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

            # SEND NOTIFICATION
            print("REVIEW SAVED")

            handle_event("review", {
                "product_name": product.title,
                "username": request.user.username,
                "rating": review.rating,
                "comment": review.comment
            })

            print("NOTIFICATION SENT")

            return JsonResponse({'success': True})

        return JsonResponse({'error': 'Invalid form'}, status=400)

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

            try:
                send_mail(
                    subject='Activate your AgroShop account',
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                )
            except Exception as e:
                print("EMAIL ERROR:", e)

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

           # SEND NOTIFICATION (Django way)
            try:
                handle_event("user_registered", {
                    "username": user.username,
                    "email": user.email,
                    "created_at": str(datetime.datetime.now())
                })
                print("USER REGISTRATION NOTIFICATION SENT")
            except Exception as e:
                print("User notification failed:", e)

            user.save()

            return render(request, 'app/activation_success.html')
        else:
            return HttpResponse("Activation link is invalid!")

class ProfileView(View):
    def get(self, request):
        form = CustomerProfileForm()
        add = Customer.objects.filter(user=request.user)
        return render(request, 'app/profile.html', {'form': form, 'add': add, 'has_address': add.exists() })

    def post(self, request):
        form = CustomerProfileForm(request.POST)
        add = Customer.objects.filter(user=request.user) 
        if form.is_valid():
            reg = form.save(commit=False)
            reg.user = request.user
            reg.save()
            messages.success(request, 'A New Address Added Successfully')
            return redirect('address')
            #form = CustomerProfileForm()
        else:
            messages.warning(request, 'Invalid Input Data')
        return render(request, 'app/profile.html', {'form': form, 'add': add, 'has_address': add.exists() })  
        
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

@login_required
def add_to_cart(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

    user = request.user
    product_id = request.POST.get("product_id")
    buy_now = request.POST.get("buy_now") == "true"

    product = get_object_or_404(Product, pk=product_id)

    if product.stock_quantity <= 0:
        return JsonResponse({"success": False, "error": "Product out of stock"}, status=400)

    cart_item = Cart.objects.filter(user=user, product=product).first()

    if cart_item:
        if cart_item.quantity >= product.stock_quantity:
            return JsonResponse({"success": False, "error": "Not enough stock"}, status=400)

        cart_item.quantity += 1
        cart_item.save()
    else:
        Cart.objects.create(user=user, product=product, quantity=1)

    cart_count = Cart.objects.filter(user=user).count()

    if buy_now:
        return redirect("showcart")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "cart_count": cart_count
        })

    return redirect(request.META.get("HTTP_REFERER", "home"))

def show_cart(request):
    user = request.user
    cart = Cart.objects.filter(user=user)

    # VALIDATE STOCK
    for item in cart:
        if item.quantity > item.product.stock_quantity:
            item.quantity = item.product.stock_quantity
            item.save()

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
        product = cart_item.product

        # STOCK CHECK
        if cart_item.quantity >= product.stock_quantity:
            return JsonResponse({
                'error': 'Max stock reached',
                'quantity': cart_item.quantity,
                'product_id': product.id,
                'item_total': float(cart_item.quantity * product.discounted_price),
                'amount': float(calculate_cart_totals(user)[0]),
                'totalamount': float(calculate_cart_totals(user)[2]),
            })

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

         # STOCK VALIDATION
        for item in cart_items:
            if item.quantity > item.product.stock_quantity:
                messages.error(request, f"Not enough stock for {item.product.title}")
                return redirect('showcart')

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
        'Paid': 20,
        'Accepted': 25,
        'Packed': 50,
        'On The Way': 75,
        'Delivered': 100,
        'Cancelled': 100,
    }

    status_color = {
        'Pending': 'secondary',
        'Paid': 'success',
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
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        custid = request.POST.get("custid")

        if not custid:
            return JsonResponse({"error": "Select address"}, status=400)
        
        try:
            customer = Customer.objects.get(id=custid, user=request.user)
        except Customer.DoesNotExist:
            return JsonResponse({"error": "Invalid address selected"}, status=400)

        cart_items = (
            Cart.objects
            .filter(user=request.user)
            .select_related("product")
        )

        if not cart_items.exists():
            return JsonResponse({"error": "Cart empty"}, status=400)

        # STOCK CHECK
        for item in cart_items:
            if item.quantity > item.product.stock_quantity:
                return JsonResponse({
                    "error": f"Not enough stock for {item.product.title}"
                }, status=400)

        shipping = Decimal("5.00")

        subtotal = sum(
            Decimal(item.quantity) * Decimal(item.product.discounted_price)
            for item in cart_items
        )

        total = subtotal + shipping

        customer = Customer.objects.get(id=custid, user=request.user)

        # SAVE CART SNAPSHOT
        cart_snapshot = [
            {
                "product_id": item.product.id,
                "title": item.product.title,
                "quantity": item.quantity,
                "price": str(item.product.discounted_price),
            }
            for item in cart_items
        ]

        # Create Payment (pending)
        payment = Payment.objects.create(
            user=request.user,
            customer=customer,
            amount=total,
            paid=False,
            status="PENDING",
            provider="montonio",
            cart_snapshot=cart_snapshot,
        )       

        # 3. Montonio payment session
        try:
            response = create_montonio_payment(payment)
            print("MONTONIO FULL RESPONSE:", response)

        except Exception as e:
            print("Montonio request failed:", e)
            payment.status = "FAILED"
            payment.save()
            return JsonResponse({"error": "Payment provider error"}, status=500)

        # Ja Montonio atgriež kļūdu
        if not response or "uuid" not in response:
            print("Montonio error:", response)
            payment.status = "FAILED"
            payment.save()
            return JsonResponse({"error": "Payment creation failed"}, status=500)

        # Saglabā payment info
        payment.transaction_id = response.get("uuid")
        payment.status = response.get("paymentStatus", "PENDING")       
        payment.save()

        # izmanto paymentUrl no API
        payment_url = response.get("paymentUrl")

        if not payment_url:
            print("Missing paymentUrl:", response)
            payment.status = "FAILED"
            payment.save()
            return JsonResponse({"error": "Payment URL missing"}, status=500)

        return redirect(payment_url)


def finalize_paid_order(payment):
    existing_order = Order.objects.filter(payment=payment).first()
    if existing_order:
        return existing_order, []

    if not payment.cart_snapshot:
        raise Exception("Payment cart_snapshot is empty")

    low_stock_products = []

    with transaction.atomic():
        order = Order.objects.create(
            user=payment.user,
            customer=payment.customer,
            total_amount=payment.amount,
            payment=payment,
            status="Paid"
        )

        for item in payment.cart_snapshot:
            product = Product.objects.select_for_update().get(id=item["product_id"])
            qty = int(item["quantity"])

            if product.stock_quantity < qty:
                raise Exception(f"Not enough stock for {product.title}")

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty
            )

            product.stock_quantity -= qty
            product.save()

            print(f"STOCK UPDATED: {product.title} -> {product.stock_quantity}")

            if product.stock_quantity < 5:
                low_stock_products.append({
                    "product_name": product.title,
                    "quantity": product.stock_quantity
                })

        Cart.objects.filter(user=payment.user).delete()
        print("CART CLEARED")

        payment.status = "PAID"
        payment.paid = True
        payment.save()

        order.status = "Paid"
        order.save()

        print("ORDER MARKED AS PAID")

        return order, low_stock_products

@csrf_exempt
def montonio_webhook(request):
    print("=== WEBHOOK HIT ===")
    print("METHOD:", request.method)
    print("HEADERS:", dict(request.headers))

    try:
        if request.body:
            try:
                data = json.loads(request.body)
            except Exception:
                data = request.POST.dict()
        else:
            data = request.POST.dict()

        print("DATA:", data)

        token = data.get("orderToken")

        if not token:
            print("NO TOKEN")
            return JsonResponse({"error": "No token"}, status=400)

        decoded = jwt.decode(
            token,
            settings.MONTONIO_SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_iat": False}
        )

        print("DECODED:", decoded)

        status = decoded.get("paymentStatus")
        merchant_ref = decoded.get("merchantReference")

        if not merchant_ref:
            return JsonResponse({"error": "No merchant reference"}, status=400)

        payment_id = str(merchant_ref).split("-")[0]
        print("PAYMENT ID:", payment_id)

        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return JsonResponse({"error": "Payment not found"}, status=404)

        if payment.paid:
            print("PAYMENT ALREADY PROCESSED")
            return JsonResponse({"ok": True})

        if status == "PAID":
            print("PROCESSING PAID ORDER")

            order, low_stock_products = finalize_paid_order(payment)

            print("ORDER CREATED:", order.id)

            for product_data in low_stock_products:
                try:
                    async_to_sync(handle_event)("stock", {
                        "product_name": product_data["product_name"],
                        "quantity": product_data["quantity"]
                    })
                    print("STOCK NOTIFICATION SENT")
                except Exception as e:
                    print("Stock notification failed:", e)

            try:
                async_to_sync(handle_event)("payment", {
                    "order_id": order.id,
                    "username": order.user.username,
                    "amount": float(order.total_amount)
                })
                print("PAYMENT NOTIFICATION SENT")
            except Exception as e:
                print("Payment notification failed:", e)

        elif status in ["CANCELLED", "FAILED"]:
            print(f"PAYMENT {status}")

            payment.status = status
            payment.paid = False
            payment.save()

            print("PAYMENT MARKED AS CANCELLED/FAILED")

        else:
            print("UNKNOWN STATUS:", status)

        return JsonResponse({"ok": True})

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return JsonResponse({"error": "Webhook failed"}, status=500)

def payment_success(request):
    token = request.GET.get("order-token")

    if not token:
        return HttpResponse("Missing token", status=400)

    try:
        decoded = jwt.decode(
            token,
            settings.MONTONIO_SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_iat": False}
        )

        status = decoded.get("paymentStatus")
        merchant_ref = decoded.get("merchantReference")

        payment_id = str(merchant_ref).split("-")[0]

        payment = Payment.objects.filter(id=payment_id).first()

        # fallback update (ja webhook nav bijis)
        if payment and status == "PAID":
            order, low_stock_products = finalize_paid_order(payment)

        # CANCEL → failed page
        if status != "PAID":
            messages.warning(request, "Payment was cancelled.")
            return redirect('showcart')

        # SUCCESS
        return render(request, "app/payment_success.html")

    except Exception as e:
        print("payment_success error:", e)
        return HttpResponse("Error", status=500)

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


@csrf_exempt
def notify(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)

        event_type = data.get("event_type")
        payload = data.get("data")

        if not event_type or not payload:
            return JsonResponse({"error": "Invalid payload"}, status=400)

        handle_event(event_type, payload)

        return JsonResponse({"success": True})

    except Exception as e:
        print("Notification error:", e)
        return JsonResponse({"success": False, "error": str(e)}, status=500)

class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        # First call original logout logic
        response = super().dispatch(request, *args, **kwargs)

        # Clear all queued messages AFTER logout
        list(messages.get_messages(request))

        return response