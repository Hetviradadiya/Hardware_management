from rest_framework import viewsets,filters,permissions
from rest_framework.permissions import IsAuthenticated
from ..models import Purchase
from ..serializers import PurchaseSerializer

class PurchaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Purchase.objects.all().order_by('-date')
    serializer_class = PurchaseSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'variant__product__name',      
        'supplier__name'      
    ]

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
