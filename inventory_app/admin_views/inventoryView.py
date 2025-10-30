from rest_framework import viewsets,filters
from rest_framework.permissions import IsAuthenticated
from ..models import Inventory
from ..serializers import InventorySerializer
from inventory_app.pagination import ListPagination

class InventoryViewSet(viewsets.ModelViewSet):
    pagination_class = ListPagination
    permission_classes = [IsAuthenticated]
    queryset = Inventory.objects.all().order_by('-id')  # or order_by('variant__product__name')
    serializer_class = InventorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'variant__product__name',   
    ]
