from rest_framework import viewsets, permissions, filters
from rest_framework.permissions import IsAuthenticated
from ..models import ProductVariant,Product
from ..serializers import ProductSerializer,ProductVariantSerializer
from django_filters.rest_framework import DjangoFilterBackend
from inventory_app.pagination import ListPagination

class ProductView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = ListPagination
    queryset = Product.objects.all().prefetch_related("variants").order_by('-id')
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "category__name"]
    filterset_fields = ["category"]

class ProductVariantView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = ListPagination
    queryset = ProductVariant.objects.all().order_by('-id')
    serializer_class = ProductVariantSerializer