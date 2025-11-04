from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.home),
    path("aboutus/", views.aboutus, name="aboutus"),
    path("contact/", views.contact, name="contact"),       
    path("category/<slug:val>", views.CategoryView.as_view(), name="category"),
    path("category-title/<val>", views.CategoryTitleView.as_view(), name="category-title"),
    path("product/<int:pk>", views.ProductDetailView.as_view(), name="product"),

    # Customer Registration
    path("registration/", views.CustomerRegistrationView.as_view(), name="customerregistration"),
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)