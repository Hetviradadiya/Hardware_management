from rest_framework import viewsets,filters,permissions
from rest_framework.permissions import IsAuthenticated
from ..models import Purchase
from ..serializers import PurchaseSerializer
from rest_framework import status
from rest_framework.response import Response
from inventory_app.pagination import ListPagination 

class PurchaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = ListPagination
    queryset = Purchase.objects.all().order_by('-date', '-id')
    serializer_class = PurchaseSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'variant__product__name',      
        'supplier__name'      
    ]
    
    def create(self, request, *args, **kwargs):
        """
        Override to allow multiple products at once for the same supplier.
        """
        supplier_id = request.data.get("supplier")
        products = request.data.get("products", [])

        if not supplier_id or not products:
            return Response({"error": "Supplier and products are required."}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        errors = []

        for prod in products:
            data = {
                "supplier": supplier_id,
                "variant": prod.get("variant"),
                "quantity": prod.get("quantity"),
                "purchase_price": prod.get("purchase_price"),
                "discount": prod.get("discount", 0),
                "gst": prod.get("gst", 0),
            }
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                serializer.save()
                created.append(serializer.data)
            else:
                errors.append(serializer.errors)

        if errors:
            return Response({"created": created, "errors": errors}, status=status.HTTP_207_MULTI_STATUS)  # Partial success
        return Response({"created": created}, status=status.HTTP_201_CREATED)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import Inventory
from ..serializers import InventoryVariantSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def purchase_products(request):
    category_id = request.GET.get("category_id")
    inventory_qs = Inventory.objects.filter(quantity__gt=0).select_related("variant__product__category")

    if category_id:
        inventory_qs = inventory_qs.filter(variant__product__category_id=category_id)

    serializer = InventoryVariantSerializer(inventory_qs, many=True)
    return Response(serializer.data)
