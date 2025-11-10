from django.contrib import admin
from .models import Customer, Product, Cart, Payment, Order, Wishlist
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.auth.models import Group

# Register your models here.
@admin.register(Product)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'selling_price', 'discounted_price', 'category', 'product_image')
    list_editable = ('selling_price', 'discounted_price', 'category')

@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'locality', 'city', 'mobile', 'zipcode', 'country')
    list_editable = ('name', 'locality', 'city', 'mobile', 'zipcode', 'country')

@admin.register(Cart)
class CartModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'products', 'quantity', 'total_cost')
    list_editable = ('quantity',)
    def products(self, obj):
        linked_product = reverse("admin:app_product_change", args=[obj.product.pk])
        return format_html('<a href="{}">{}</a>', linked_product, obj.product.title)

@admin.register(Payment)
class PaymentModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'paypal_order_id', 'paypal_payment_id', 'paypal_status', 'payer_email', 'paid',
        'created_at')
    list_editable = ('paid',)
    list_filter = ('paid', 'paypal_status', 'created_at')
    search_fields = ('user__username', 'paypal_order_id', 'paypal_payment_id', 'payer_email')
    ordering = ('-created_at',)

@admin.register(Order)
class OrderModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'customers', 'products', 'quantity', 'status', 'payments', 'ordered_date', 'total_cost_display')
    list_filter = ('status', 'ordered_date',)
    search_fields = ('user__username', 'customer__name', 'product__title', 'payment__paypal_payment_id')
    ordering = ('-ordered_date',)
    list_editable = ('status',)
    readonly_fields = ('total_cost_display',)

    def total_cost_display(self, obj):
        return f"€{obj.total_cost:.2f}"
    total_cost_display.short_description = 'Total Cost'

    def customers(self, obj):
        linked_customer = reverse("admin:app_customer_change", args=[obj.customer.pk])
        return format_html('<a href="{}">{}</a>', linked_customer, obj.customer.name)
    def products(self, obj):
        linked_product = reverse("admin:app_product_change", args=[obj.product.pk])
        return format_html('<a href="{}">{}</a>', linked_product, obj.product.title)
    def payments(self, obj):
        linked_payment = reverse("admin:app_payment_change", args=[obj.payment.pk])
        return format_html('<a href="{}">{}</a>', linked_payment, obj.payment.paypal_payment_id)

@admin.register(Wishlist)
class WishlistModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'products')
    search_fields = ('user__username', 'product__title',)
    def products(self, obj):
        linked_product = reverse("admin:app_product_change", args=[obj.product.pk])
        return format_html('<a href="{}">{}</a>', linked_product, obj.product.title)

admin.site.unregister(Group)