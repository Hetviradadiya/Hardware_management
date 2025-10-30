from rest_framework.views import APIView
from ..serializers import *
from rest_framework.response import Response
from rest_framework import generics,viewsets,permissions,filters
from ..models import *
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from inventory_app.pagination import ListPagination 
class SupplierView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = ListPagination
    queryset=Supplier.objects.all().order_by('-id')
    serializer_class=SupplierSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'name','email','phone','address'      
    ]

@api_view(["GET"])
@permission_classes([IsAuthenticated])    
def supplier_purchases(request, pk):
    purchases = Purchase.objects.filter(supplier=pk).order_by("-date")

    # Optional date filtering
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    if start_date and end_date:
        purchases = purchases.filter(date__range=[parse_date(start_date), parse_date(end_date)])
        
    paginator = ListPagination()
    query_params = getattr(request, "query_params", request.GET)
    result_page = paginator.paginate_queryset(purchases, request)

    data = [
        {
            "id": p.id,
            "date": p.date.strftime("%Y-%m-%d"),
            "variant": str(p.variant),
            "quantity": p.quantity,
            "purchase_price": str(p.purchase_price),
            "discount": str(p.discount),
            "gst": str(p.gst),
            "total_price": str(p.total_price),
        }
        for p in result_page
    ]

    return paginator.get_paginated_response(data)