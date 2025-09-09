from rest_framework.views import APIView
from ..serializers import *
from rest_framework.response import Response
from rest_framework import generics,viewsets,permissions,filters
from ..models import *


class CustomerView(viewsets.ModelViewSet):
    queryset=Customer.objects.all()
    serializer_class=CustomerSerializer
    # permission_classes=[permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'name','email','phone','address'      
    ]
