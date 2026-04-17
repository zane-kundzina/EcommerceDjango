from django.db import models
from django.contrib.auth.models import User

CATEGORY_CHOICES = (
    ('VG', 'Vegetables'),
    ('FR', 'Fruits'),
    ('GR', 'Grains'),
    ('DP', 'Dairy Products'),
    ('MT', 'Meat'),
    ('NS', 'Nuts and Seeds'),
)

COUNTRY_CHOICES = (
    ('Albania', 'Albania'),
    ('Austria', 'Austria'),
    ('Belgium', 'Belgium'),
    ('Bulgaria', 'Bulgaria'),
    ('Croatia', 'Croatia'),
    ('Cyprus', 'Cyprus'),
    ('Czech Republic', 'Czech Republic'),
    ('Denmark', 'Denmark'),
    ('Estonia', 'Estonia'),
    ('Finland', 'Finland'),
    ('France', 'France'),
    ('Germany', 'Germany'),
    ('Greece', 'Greece'),
    ('Hungary', 'Hungary'),
    ('Iceland', 'Iceland'),
    ('Ireland', 'Ireland'),
    ('Italy', 'Italy'),
    ('Latvia', 'Latvia'),
    ('Lithuania', 'Lithuania'),
    ('Luxembourg', 'Luxembourg'),
    ('Malta', 'Malta'),
    ('Netherlands', 'Netherlands'),
    ('Norway', 'Norway'),
    ('Poland', 'Poland'),
    ('Portugal', 'Portugal'),
    ('Romania', 'Romania'),
    ('Slovakia', 'Slovakia'),
    ('Slovenia', 'Slovenia'),
    ('Spain', 'Spain'),
    ('Sweden', 'Sweden'),
    ('Switzerland', 'Switzerland'),
    ('United Kingdom', 'United Kingdom'),
)

STATUS_CHOICES = (
    ('Pending', 'Pending'),
    ('Accepted', 'Accepted'),
    ('Packed', 'Packed'),
    ('On The Way', 'On The Way'),
    ('Delivered', 'Delivered'),
    ('Cancelled', 'Cancelled'),
)

PAYMENT_STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("PAID", "Paid"),
    ("FAILED", "Failed"),
]

class Product(models.Model):
    title = models.CharField(max_length=100)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    composition = models.TextField(default='')
    prodapp = models.TextField(default='')
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    product_image = models.ImageField(upload_to='product')
    stock_quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title
    
    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / reviews.count(), 1)
    
class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    locality = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    mobile = models.CharField(max_length=12)
    zipcode = models.CharField(max_length=10)
    country = models.CharField(choices=COUNTRY_CHOICES, max_length=50)

    def __str__(self):
        return self.name
    
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_cost(self):
        return self.quantity * self.product.discounted_price
    
    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return str(self.id)
    
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    provider = models.CharField(max_length=50, default="montonio") 
    transaction_id = models.CharField(max_length=255, blank=True, null=True) 
    status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='Pending')

    paid = models.BooleanField(default=False)    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider} | {self.amount} | {self.status}"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)    
    ordered_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_cost(self):
        return self.quantity * self.product.discounted_price

    def __str__(self):
        return f"{self.product.title} x {self.quantity}"
    
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"Wishlist {self.id} - {self.user.username}"


class Review(models.Model):
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)  # 1-5 rating
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)     

    class Meta:
        ordering = ['-created_at']  # newest first

    def __str__(self):
        return f"{self.user.username} - {self.product.title}"
    
    @property
    def empty_stars(self):
        return 5 - self.rating
