from django.contrib import messages
from django.db.models import Count
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from .models import Product
from .forms import CustomerRegistrationForm

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