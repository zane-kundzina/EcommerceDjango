from django.contrib import admin
from .models import Customer, Product, Cart

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
    list_display = ('id', 'user', 'product', 'quantity', 'total_cost')
    list_editable = ('quantity',)