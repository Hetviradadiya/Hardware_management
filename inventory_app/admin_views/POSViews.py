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

    # Order-level discount from form
    order_discount = Decimal(request.POST.get("order_discount", "0"))
    is_percentage = request.POST.get("is_percentage", "false") == "true"

    # Fetch all cart items
    cart_items = Cart.objects.all()
    if not cart_items.exists():
        return redirect("cart_page")  # No items in cart

    # Step 1: Calculate totals from cart
    subtotal = Decimal(0)
    total_item_discount = Decimal(0)
    total_gst = Decimal(0)

    for cart_item in cart_items:
        item_total = cart_item.variant.price * cart_item.quantity
        subtotal += item_total

        # Calculate item discount
        if cart_item.is_percentage:
            item_discount_val = (item_total * cart_item.item_discount) / Decimal(100)
        else:
            item_discount_val = cart_item.item_discount
        total_item_discount += item_discount_val

        # Calculate GST on discounted price
        total_gst += ((item_total - item_discount_val) * cart_item.gst) / Decimal(100)

    # Order-level discount
    if is_percentage:
        order_discount_val = (subtotal * order_discount) / Decimal(100)
    else:
        order_discount_val = order_discount

    total_discount = total_item_discount + order_discount_val
    grand_total = subtotal - total_discount + total_gst

    # Step 2: Create Order
    order = Order.objects.create(
        customer=customer,
        subtotal=subtotal,
        total_item_discount=total_item_discount,
        order_discount=order_discount,
        is_percentage=is_percentage,
        total_discount=total_discount,
        total_gst=total_gst,
        total_amount=grand_total,
    )

    # Step 3: Create OrderItems
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

        # Step 4: Deduct inventory
        inventory_item = Inventory.objects.get(variant=cart_item.variant)
        inventory_item.quantity -= cart_item.quantity
        inventory_item.save()

    # Step 5: Create Sale & calculate profit
    sale = Sale.objects.create(order=order)
    sale.save()  # your Sale.save() handles profit calculation

    # Step 6: Clear cart
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