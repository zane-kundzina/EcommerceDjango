from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_view
from .forms import LoginForm
from .forms import MyPasswordResetForm, MyPasswordChangeForm, MySetPasswordForm
from django.contrib import admin

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
    path('deleteaddress/<int:pk>/', views.delete_address, name='deleteaddress'),

    path("add-to-cart/", views.add_to_cart, name="add-to-cart"),
    path("cart/", views.show_cart, name="showcart"),
    path("checkout/", views.checkout.as_view(), name="checkout"),
    #path("paymentdone/", views.payment_done, name="paymentdone"),
    path('capture-payment/', views.CapturePaymentView.as_view(), name='capture-payment'),
    path('create-order/', views.CreateOrderView.as_view(), name='create-order'),
    path("orders/", views.orders, name="orders"),

    path("search/", views.search, name="search"),

    path("pluscart/", views.plus_cart, name="pluscart"),
    path("minuscart/", views.minus_cart, name="minuscart"),    
    path("removecart/", views.remove_cart, name="removecart"),
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path('pluswishlist/', views.plus_wishlist, name='pluswishlist'),
    path('minuswishlist/', views.minus_wishlist, name='minuswishlist'),

    # Customer Registration
    path("registration/", views.CustomerRegistrationView.as_view(), name="customerregistration"),
    path("accounts/login/", auth_view.LoginView.as_view(template_name='app/login.html', authentication_form=LoginForm), name="login"),     
    path('passwordchange/', auth_view.PasswordChangeView. as_view(template_name='app/changepassword.html', form_class=MyPasswordChangeForm, success_url='/passwordchangedone/'), name='passwordchange'),    
    path('passwordchangedone/', auth_view.PasswordChangeDoneView.as_view(template_name='app/passwordchangedone.html'), name='passwordchangedone'),   
    path("logout/", auth_view.LogoutView.as_view(next_page='/accounts/login/'), name="logout"),

    path('password_reset/', auth_view.PasswordResetView.as_view(
    template_name='app/passwordreset.html',
    form_class=MyPasswordResetForm
), name='password_reset'),

    path('password_reset/done/', auth_view.PasswordResetDoneView.as_view(template_name='app/passwordresetdone.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_view.PasswordResetConfirmView.as_view(template_name='app/passwordresetconfirm.html', form_class=MySetPasswordForm), name='password_reset_confirm'),
    path('reset/done/', auth_view.PasswordResetCompleteView.as_view(template_name='app/passwordresetcomplete.html'),name='password_reset_complete'),

]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Online Shop Admin"    
admin.site.site_title = "Online Shop Admin Portal"
admin.site.index_title = "Welcome to Online Shop Admin Portal"