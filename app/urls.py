from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_view
from .forms import LoginForm
from .forms import MyPasswordResetForm

urlpatterns = [
    path("", views.home),
    path("aboutus/", views.aboutus, name="aboutus"),
    path("contact/", views.contact, name="contact"),       
    path("category/<slug:val>", views.CategoryView.as_view(), name="category"),
    path("category-title/<val>", views.CategoryTitleView.as_view(), name="category-title"),
    path("product/<int:pk>", views.ProductDetailView.as_view(), name="product"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("address/", views.address, name="address"),
    path('updateaddress/<int:pk>/', views.UpdateAddressView.as_view(), name='updateaddress'),

    # Customer Registration
    path("registration/", views.CustomerRegistrationView.as_view(), name="customerregistration"),
    path("accounts/login/", auth_view.LoginView.as_view(template_name='app/login.html', authentication_form=LoginForm), name="login"), 
    path("password-reset/", auth_view.PasswordResetView.as_view(template_name='app/password_reset.html',form_class=MyPasswordResetForm), name="password_reset"),

]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)