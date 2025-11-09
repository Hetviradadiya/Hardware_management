from rest_framework import viewsets, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from datetime import datetime
import pytz
from ..models import Cart, ProductVariant,Customer, Order, OrderItem, Sale, Inventory
from django.shortcuts import render,redirect
from ..serializers import CartSerializer,OrderItemSerializer
from decimal import Decimal

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        variant_id = request.data.get("variantId")
        qty = int(request.data.get("qty", 1))
        price = request.data.get("price")
        replace = request.data.get("replace", False)

        if not variant_id:
            return Response({"error": "variantId is required"}, status=status.HTTP_400_BAD_REQUEST)

        variant = get_object_or_404(ProductVariant, id=variant_id)
        final_price = Decimal(price) if price else variant.price

        cart_item, created = Cart.objects.get_or_create(
            variant=variant,
            defaults={"quantity": qty,"price": final_price, "item_discount": 0, "is_percentage": True, "gst": 0}
        )

        if not created:
            if replace:
                cart_item.quantity = qty
            else:
                cart_item.quantity += qty
            cart_item.price = final_price
            cart_item.save()

        serializer = self.get_serializer(cart_item)
        return Response({"success": True, "cart_item": serializer.data}, status=status.HTTP_200_OK)

    def partial_update(self, request, pk=None):
        cart_item = self.get_object()
        data = request.data

        # Only update if the key exists in data
        if "quantity" in data:
            qty = data.get("quantity")
            if qty not in [None, ""]:
                cart_item.quantity = int(qty)
                
        if "price" in data:
            price_value = data.get("price")
            if price_value in [None, ""]:
                # If empty or null, fallback to variant price
                cart_item.price = cart_item.variant.price
            else:
                cart_item.price = Decimal(price_value)

        if "item_discount" in data:
            item_discount = data.get("item_discount")
            if item_discount in [None, ""]:
                cart_item.item_discount = Decimal(0)
            else:
                cart_item.item_discount = Decimal(item_discount)

        if "is_percentage" in data:
            cart_item.is_percentage = data.get("is_percentage", cart_item.is_percentage)

        if "gst" in data:
            gst_value = data.get("gst")
            if gst_value in [None, ""]:
                cart_item.gst = Decimal(0)
            else:
                cart_item.gst = Decimal(gst_value)

        cart_item.save()
        serializer = CartSerializer(cart_item, context={"request": request})
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        cart_item = self.get_object()
        cart_item.delete()
        return Response({"success": True}, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect

def place_order(request):
    customer_id = request.POST.get("customer_id")
    customer = get_object_or_404(Customer, id=customer_id)

    # Read already-calculated values from frontend
    subtotal = to_decimal(request.POST.get("subtotal"))
    total_item_discount = to_decimal(request.POST.get("total_item_discount"))
    order_discount_flat = to_decimal(request.POST.get("order_discount_flat"))
    order_discount_percent = to_decimal(request.POST.get("order_discount_percent"))
    total_discount = to_decimal(request.POST.get("total_discount"))
    total_gst = to_decimal(request.POST.get("total_gst"))
    total_amount = to_decimal(request.POST.get("total_amount"))
    paid_amount = to_decimal(request.POST.get("paid_amount"))
    pay_type = request.POST.get("pay_type")

    # Create Order - let Django auto_now_add handle the timezone properly
    order = Order.objects.create(
        customer=customer,
        subtotal=subtotal,
        total_item_discount=total_item_discount,
        order_discount=order_discount_flat,
        is_percentage=False,
        total_discount=total_discount,
        total_gst=total_gst,
        total_amount=total_amount,
        pay_type=pay_type,
        paid_amount=paid_amount,
    )

    # ---------------- Payment Calculation ----------------
    final_total = float(total_amount)
    paid_amount_float = float(paid_amount)
    old_unpaid = float(customer.pending_amount or 0.0)
    old_advance = float(customer.advance_payment or 0.0)

    order_balance = 0.0  # New pending for this order
    order_advance = 0.0  # New advance created by this order
    is_paid = False

    # CASE 1: Paid >= Current Order
    if paid_amount_float >= final_total:
        extra = paid_amount_float - final_total
        order_balance = 0.0

        if extra > 0:
            # Use extra to clear old unpaid first
            if extra >= old_unpaid:
                extra -= old_unpaid
                old_unpaid = 0.0
                order_advance = extra
                is_paid = True
            else:
                old_unpaid -= extra
                # Use old advance to clear remaining unpaid
                if old_advance >= old_unpaid:
                    old_advance -= old_unpaid
                    old_unpaid = 0.0
                    is_paid = True
                else:
                    old_unpaid -= old_advance
                    old_advance = 0.0
                    is_paid = False
                order_advance = 0.0
                order_balance = old_unpaid
        else:
            order_advance = 0.0
            order_balance = old_unpaid
            is_paid = (old_unpaid == 0)

    # CASE 2: Paid < Current Order
    else:
        remaining_due = final_total - paid_amount_float
        if old_advance >= remaining_due:
            old_advance -= remaining_due
            remaining_due = 0.0
            order_balance = 0.0
            is_paid = True
        else:
            remaining_due -= old_advance
            old_advance = 0.0
            order_balance = old_unpaid + remaining_due
            is_paid = False
        order_advance = 0.0

    # Update customer & order
    customer.advance_payment = Decimal(old_advance + order_advance)
    customer.pending_amount = Decimal(order_balance)
    customer.save()

    order.is_paid = is_paid
    order.save()

    # ---------------- Save OrderItems ----------------
    cart_items = Cart.objects.all()
    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            variant=cart_item.variant,
            quantity=cart_item.quantity,
            price_at_sale=cart_item.variant.price,
            item_discount=cart_item.item_discount,
            is_percentage=cart_item.is_percentage,
            gst=cart_item.gst,
        )

    # ---------------- Create Sale ----------------
    Sale.objects.create(order=order, total_amount=total_amount, paid_amount=paid_amount)

    # Clear cart
    cart_items.delete()

    # Redirect to invoice/bill page
    return redirect("bill_page", order_id=order.id)

def to_decimal(value):
    try:
        return Decimal(str(value).strip() or "0")
    except:
        return Decimal("0")
    
def bill_page(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all()
    serializer = OrderItemSerializer(items, many=True)
    
    # Calculate net amount after returns
    net_amount = order.get_net_amount() if hasattr(order, 'get_net_amount') else order.total_amount

    return render(request, "bill_page.html", {
        "order": order,
        "items": serializer.data,
        "net_amount": net_amount
    })