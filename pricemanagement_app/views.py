from rest_framework.views import APIView
from pricemanagement_app.serializers import *
from rest_framework.response import Response
from rest_framework import generics,viewsets,permissions,filters
from pricemanagement_app.models import *
from django.http import JsonResponse
from django.utils.dateparse import parse_date

class ProductViewset(viewsets.ModelViewSet):
    queryset=Product.objects.all()
    serializer_class=ProductSerializer
    # permission_classes=[permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'name','size','hsn_code','pcs_size'
    ]