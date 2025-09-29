from rest_framework import viewsets, permissions, filters
from rest_framework.permissions import IsAuthenticated
from ..models import ProductVariant,Product
from ..serializers import ProductSerializer,ProductVariantSerializer
from django_filters.rest_framework import DjangoFilterBackend

class ProductView(viewsets.ModelViewSet):
    queryset = Product.objects.all().prefetch_related("variants")
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "category__name"]
    filterset_fields = ["category"]

class ProductVariantView(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAuthenticated]