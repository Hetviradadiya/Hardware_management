from django.shortcuts import render, get_object_or_404
from ..models import Customer, Order
from rest_framework.decorators import api_view
from ..serializers import Orderserializer
from rest_framework.response import Response

@api_view(["GET"])
def customer_orders(request,pk):
    # customer = get_object_or_404(Customer, id=id)
    orders = Order.objects.filter(customer=pk).order_by("-order_date")  
    
    serializer = Orderserializer(orders, many=True)
    return Response(serializer.data)
    
@api_view(["GET"])
def order_detail_api(request, id):
    order = get_object_or_404(Order, id=id)
    serializer = Orderserializer(order)
    return Response(serializer.data)