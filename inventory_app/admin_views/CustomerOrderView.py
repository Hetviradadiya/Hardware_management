from django.shortcuts import render, get_object_or_404
from ..models import Customer, Order
from rest_framework.decorators import api_view
from ..serializers import OrderSerializer
from rest_framework.response import Response
from datetime import datetime
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from inventory_app.pagination import ListPagination

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def customer_orders(request, pk):
    orders = Order.objects.filter(customer=pk).order_by("-order_date")

    # Get date filter params
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            # filter between dates (inclusive)
            orders = orders.filter(order_date__date__range=[start, end])
        except Exception as e:
            print("Invalid date filter:", e)

    paginator = ListPagination()
    result_page = paginator.paginate_queryset(orders, request)
    serializer = OrderSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)
    
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_detail_api(request, id):
    order = get_object_or_404(Order, id=id)
    serializer = OrderSerializer(order)
    return Response(serializer.data)