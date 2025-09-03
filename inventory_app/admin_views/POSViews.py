from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ..models import Cart, ProductVariant,Customer, Order, OrderItem, Sale
from django.shortcuts import render,redirect
from ..serializers import CartSerializer,OrderItemSerializer

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        variant_id = request.data.get("variantId")
        qty = int(request.data.get("qty", 1))
        replace = request.data.get("replace", False)

        if not variant_id:
            return Response({"error": "variantId is required"}, status=status.HTTP_400_BAD_REQUEST)

        variant = get_object_or_404(ProductVariant, id=variant_id)

        # Add or update quantity
        cart_item, created = Cart.objects.get_or_create(
            variant=variant,
            defaults={"quantity": qty}
        )
        if not created:
            if replace:
                cart_item.quantity = qty
            else:
                cart_item.quantity += qty
            cart_item.save()

        serializer = self.get_serializer(cart_item)
        return Response({"success": True, "cart_item": serializer.data}, status=status.HTTP_200_OK)

def place_order(request):
    customer_id = request.POST.get("customer_id")
    customer = get_object_or_404(Customer, id=customer_id)

    cart_items = Cart.objects.all()
    if not cart_items.exists():
        return redirect("cart_page")

    order = Order.objects.create(customer=customer, total_amount=0)

    for cart_item in cart_items:
        price = cart_item.variant.price
        OrderItem.objects.create(
            order=order,
            variant=cart_item.variant,
            quantity=cart_item.quantity,
            price_at_sale=price,
            item_discount=cart_item.discount or 0,  # take product discount from cart
            is_percentage=True   # or True if you store %
        )

    order.total_amount = order.calculate_total()
    order.save()

    Sale.objects.create(order=order, total_amount=order.total_amount)
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