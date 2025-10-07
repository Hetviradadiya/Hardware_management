from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum
from django.utils.timezone import now, make_aware
from datetime import datetime, timedelta

from inventory_app.models import (
    Category, Supplier, Customer,
    Product, ProductVariant, Purchase,Order,Inventory
)


class DashboardStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        is_admin = user.is_superuser or (hasattr(user, "role") and user.role.name in ["Admin"])

        today = now().date()
        ten_days_ago = today - timedelta(days=10)
        today_start = make_aware(datetime.combine(today, datetime.min.time()))
        today_end = make_aware(datetime.combine(today, datetime.max.time()))

        # Filters for staff vs admin
        product_filter = Q()
        purchase_filter = Q()
        order_filter = Q()

        if not is_admin:
            product_filter &= Q(created_by=user)
            purchase_filter &= Q(created_by=user)
            order_filter &= Q(created_by=user)

        # Totals
        total_categories = Category.objects.filter(product_filter).count()
        total_products = Product.objects.filter(product_filter).count()
        total_suppliers = Supplier.objects.count()
        total_customers = Customer.objects.count()
        total_purchases = Purchase.objects.filter(purchase_filter).count()

        # Inventory
        low_stock_products = Inventory.objects.filter(quantity__lt=5).count()

        # Orders
        today_orders = Order.objects.filter(
            order_filter,
            order_date__range=(today_start, today_end)
        ).count()

        last_10_days_orders = Order.objects.filter(
            order_filter,
            order_date__gte=ten_days_ago
        ).count()

        total_sales_amount = Order.objects.filter(order_filter).aggregate(
            total=Sum("total_amount")
        )["total"] or 0

        data = {
            "total_categories": total_categories,
            "total_products": total_products,
            "total_suppliers": total_suppliers,
            "total_customers": total_customers,
            "total_purchases": total_purchases,

            "low_stock_products": low_stock_products,
            "today_orders": today_orders,
            "last_10_days_orders": last_10_days_orders,
            "total_sales_amount": total_sales_amount,
        }

        return Response(data)


class DashboardDataAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Recent Products (5 latest)
        recent_products = list(
            Product.objects.select_related("category", "supplier")
            .order_by("-id")[:5]
            .values("id", "name", "category__name", )
        )

        # Recent Purchases
        recent_purchases = list(
            Purchase.objects.order_by("-id")[:5]
            .values("id", "date", "total_price", "supplier__name")
        )

        # Recent Customers
        recent_customers = list(
            Customer.objects.order_by("-id")[:5]
            .values("id", "name", "phone", "email")
        )

        # Recent Suppliers
        recent_suppliers = list(
            Supplier.objects.order_by("-id")[:5]
            .values("id", "name", "phone", "email")
        )

        return Response({
            "recent_products": recent_products,
            "recent_purchases": recent_purchases,
            "recent_customers": recent_customers,
            "recent_suppliers": recent_suppliers,
        })
