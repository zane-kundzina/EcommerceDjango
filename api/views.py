from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from app.models import Order
from .serializers import OrderSerializer
from app.models import Product
from .serializers import ProductSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Optional: only return orders for the logged-in user
        return self.queryset.filter(user=self.request.user)
    
class ProductViewSet(viewsets.ModelViewSet):    

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset
    

