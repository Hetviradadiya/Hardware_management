from rest_framework import viewsets, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Product, ProductPrice, Dealer
from .serializers import ProductSerializer, ProductPriceSerializer, DealerSerializer

# -------------------- PRODUCT VIEWSET --------------------
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.prefetch_related('prices__dealers', 'sizes').all().order_by('-id')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'sizes__size', 'sizes__code', 'sizes__hsn']

# -------------------- PRODUCT PRICE VIEWSET --------------------
class ProductPriceViewSet(viewsets.ModelViewSet):
    queryset = ProductPrice.objects.select_related('product').prefetch_related('dealers').all().order_by('-id')
    serializer_class = ProductPriceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['product__name', 'payment_type']

# -------------------- DEALER VIEWSET --------------------
class DealerViewSet(viewsets.ModelViewSet):
    queryset = Dealer.objects.select_related('product_price', 'product_price__product').all().order_by('-id')
    serializer_class = DealerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['dlr_name', 'slol', 'product_price__product__name']

# -------------------- BULK PRODUCT API --------------------
class BulkProductCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        products = Product.objects.prefetch_related('sizes__prices__dealers').all().order_by('-id')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # Check if we're receiving a list or single product
        if isinstance(request.data, list):
            serializer = ProductSerializer(data=request.data, many=True)
        else:
            serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, pk=None):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk=None):
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        return Response({'message': 'Product deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
