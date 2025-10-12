from rest_framework import viewsets, permissions, filters
from pricemanagement_app.models import Product, ProductPrice, Dealer
from pricemanagement_app.serializers import ProductSerializer, ProductPriceSerializer, DealerSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404

# -------------------- PRODUCT VIEWSET --------------------
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-id')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code', 'size', 'hsn']


# -------------------- PRODUCT PRICE VIEWSET --------------------
class ProductPriceViewSet(viewsets.ModelViewSet):
    queryset = ProductPrice.objects.select_related('product').all().order_by('-id')
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


class BulkProductCreateAPIView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Fetch all products with their nested prices and dealers"""
        products = Product.objects.prefetch_related(
            'prices__dealers'
        ).all().order_by('-id')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # Expecting a list of products from frontend
        serializer = ProductSerializer(data=request.data, many=True)
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