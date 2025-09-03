from rest_framework import viewsets, permissions
from ..models import ProductVariant,Product
from ..serializers import ProductSerializer,ProductVariantSerializer

class ProductView(viewsets.ModelViewSet):
    queryset = Product.objects.all().prefetch_related("variants")
    serializer_class = ProductSerializer
    # permission_classes = [permissions.IsAuthenticated]

class ProductVariantView(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    # permission_classes = [permissions.IsAuthenticated]