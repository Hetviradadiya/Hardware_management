from rest_framework.views import APIView
from ..serializers import *
from rest_framework.response import Response
from rest_framework import generics,viewsets,permissions
from ..models import *


class SupplierView(viewsets.ModelViewSet):
    queryset=Supplier.objects.all()
    serializer_class=SupplierSerializer
    permission_classes=[permissions.IsAuthenticated]
