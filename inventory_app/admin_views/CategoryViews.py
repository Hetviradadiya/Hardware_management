from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..serializers import *
from rest_framework.response import Response
from rest_framework import generics,viewsets,permissions,filters
from ..models import *
from inventory_app.pagination import ListPagination 

class CategoryView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = ListPagination
    queryset=Category.objects.all().order_by('-id')
    serializer_class=CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
