from rest_framework.views import APIView
from ..serializers import *
from rest_framework.response import Response
from rest_framework import generics,viewsets,permissions
from ..models import *


class CategoryView(viewsets.ModelViewSet):
    queryset=Category.objects.all()
    serializer_class=CategorySerializer
    permission_classes=[permissions.IsAuthenticated]
