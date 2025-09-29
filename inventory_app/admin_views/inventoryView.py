from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..models import Inventory
from ..serializers import InventorySerializer

class InventoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Inventory.objects.all().order_by('-id')  # or order_by('variant__product__name')
    serializer_class = InventorySerializer
