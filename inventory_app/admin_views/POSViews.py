from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ..models import Cart, ProductVariant,Customer, Order, OrderItem, Sale, Inventory
from django.shortcuts import render,redirect
from ..serializers import CartSerializer,OrderItemSerializer
from decimal import Decimal

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    # permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        variant_id = request.data.get("variantId")
        qty = int(request.data.get("qty", 1))
        replace = request.data.get("replace", False)

        if not variant_id:
            return Response({"error": "variantId is required"}, status=status.HTTP_400_BAD_REQUEST)

        variant = get_object_or_404(ProductVariant, id=variant_id)

        cart_item, created = Cart.objects.get_or_create(
            variant=variant,
            defaults={"quantity": qty, "item_discount": 0, "is_percentage": True, "gst": 0}
        )

        if not created:
            if replace:
                cart_item.quantity = qty
            else:
                cart_item.quantity += qty
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

def place_order(request):
    customer_id = request.POST.get("customer_id")
    customer = get_object_or_404(Customer, id=customer_id)

    # Read already-calculated values
    subtotal = Decimal(request.POST.get("subtotal", "0"))
    total_item_discount = Decimal(request.POST.get("total_item_discount", "0"))
    order_discount_flat = Decimal(request.POST.get("order_discount_flat", "0"))
    order_discount_percent = Decimal(request.POST.get("order_discount_percent", "0"))
    total_discount = Decimal(request.POST.get("total_discount", "0"))
    total_gst = Decimal(request.POST.get("total_gst", "0"))
    total_amount = Decimal(request.POST.get("total_amount", "0"))

    pay_type = request.POST.get("pay_type")
    paid_amount = Decimal(request.POST.get("paid_amount", "0"))

    # Create Order
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
        is_paid=(paid_amount >= total_amount),
    )
    
    total_paid = paid_amount
    advance_used = Decimal("0")

    if customer.advance_payment > 0:
        needed = total_amount - total_paid
        if needed > 0:
            if customer.advance_payment >= needed:
                advance_used = needed
                customer.advance_payment -= needed
                total_paid += needed
            else:
                advance_used = customer.advance_payment
                total_paid += customer.advance_payment
                customer.advance_payment = 0

    # Handle pending / overpaid
    if total_paid < total_amount:
        customer.pending_amount += (total_amount - total_paid)
    elif total_paid > total_amount:
        customer.advance_payment += (total_paid - total_amount)
        
    order.is_paid = (total_paid >= total_amount)
    order.save()

    customer.save()

    # Save each cart item
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

    # Create Sale record (profit calculation inside model save)
    Sale.objects.create(order=order, total_amount=total_amount, paid_amount=paid_amount)

    # Clear cart
    cart_items.delete()

    return redirect("bill_page", order_id=order.id)

def bill_page(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all()
    serializer = OrderItemSerializer(items, many=True)

    return render(request, "bill_page.html", {
        "order": order,
        "items": serializer.data
    })