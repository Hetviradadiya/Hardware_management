from rest_framework.views import APIView
from ..serializers import *
from rest_framework.response import Response
from rest_framework import generics,viewsets,permissions,filters
from ..models import *
from django.http import JsonResponse
from django.utils.dateparse import parse_date

class SupplierView(viewsets.ModelViewSet):
    queryset=Supplier.objects.all()
    serializer_class=SupplierSerializer
    permission_classes=[permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'name','email','phone','address'      
    ]
    
def supplier_purchases(request, pk):
    purchases = Purchase.objects.filter(supplier=pk).order_by("-date")

    # Optional date filtering
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    if start_date and end_date:
        purchases = purchases.filter(date__range=[parse_date(start_date), parse_date(end_date)])

    data = []
    for p in purchases:
        data.append({
            "id": p.id,
            "date": p.date.strftime("%Y-%m-%d"),
            "variant": str(p.variant),
            "quantity": p.quantity,
            "purchase_price": str(p.purchase_price),
            "discount": str(p.discount),
            "gst": str(p.gst),
            "total_price": str(p.total_price),
        })

    return JsonResponse(data, safe=False)