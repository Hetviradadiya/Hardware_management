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

        # Additional detailed stats
        total_inventory_value = Purchase.objects.filter(purchase_filter).aggregate(
            total=Sum("total_price")
        )["total"] or 0

        # Monthly stats
        month_start = today.replace(day=1)
        monthly_orders = Order.objects.filter(
            order_filter,
            order_date__gte=month_start
        ).count()
        
        monthly_sales = Order.objects.filter(
            order_filter,
            order_date__gte=month_start
        ).aggregate(total=Sum("total_amount"))["total"] or 0

        # Weekly stats
        week_start = today - timedelta(days=today.weekday())
        weekly_orders = Order.objects.filter(
            order_filter,
            order_date__gte=week_start
        ).count()
        
        weekly_sales = Order.objects.filter(
            order_filter,
            order_date__gte=week_start
        ).aggregate(total=Sum("total_amount"))["total"] or 0

        # Product variants count
        total_variants = ProductVariant.objects.filter(product__in=Product.objects.filter(product_filter)).count()
        
        # Critical stock (less than 3 items)
        critical_stock_products = Inventory.objects.filter(quantity__lt=3).count()
        
        # Out of stock products
        out_of_stock_products = Inventory.objects.filter(quantity=0).count()

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
            
            # New detailed stats
            "total_inventory_value": total_inventory_value,
            "monthly_orders": monthly_orders,
            "monthly_sales": monthly_sales,
            "weekly_orders": weekly_orders,
            "weekly_sales": weekly_sales,
            "total_variants": total_variants,
            "critical_stock_products": critical_stock_products,
            "out_of_stock_products": out_of_stock_products,
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

        # Recent Orders
        recent_orders = list(
            Order.objects.select_related("customer")
            .order_by("-id")[:5]
            .values("id", "order_date", "total_amount", "customer__name")
        )

        # Top selling products (based on order items)
        from django.db.models import Count, Sum as DBSum
        top_products = list(
            ProductVariant.objects
            .filter(orderitem__isnull=False)
            .annotate(
                total_sold=DBSum("orderitem__quantity"),
                order_count=Count("orderitem")
            )
            .select_related("product")
            .order_by("-total_sold")[:5]
            .values("product__name", "size", "total_sold", "order_count")
        )

        # Low stock items with details
        low_stock_items = list(
            Inventory.objects
            .select_related("variant__product")
            .filter(quantity__lt=10, quantity__gt=0)
            .order_by("quantity")[:10]
            .values("variant__product__name", "variant__size", "quantity")
        )

        # Monthly sales trend (last 6 months)
        from datetime import date
        monthly_trend = []
        for i in range(6):
            month_date = date.today().replace(day=1) - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            if i == 0:
                month_end = date.today()
            else:
                next_month = month_date.replace(day=28) + timedelta(days=4)
                month_end = (next_month - timedelta(days=next_month.day)).replace(day=1) + timedelta(days=31)
                month_end = min(month_end.replace(day=1) + timedelta(days=31) - timedelta(days=1), month_end)
            
            month_sales = Order.objects.filter(
                order_date__date__gte=month_start,
                order_date__date__lte=month_end
            ).aggregate(total=DBSum("total_amount"))["total"] or 0
            
            monthly_trend.append({
                "month": month_start.strftime("%b %Y"),
                "sales": float(month_sales)
            })

        return Response({
            "recent_products": recent_products,
            "recent_purchases": recent_purchases,
            "recent_customers": recent_customers,
            "recent_suppliers": recent_suppliers,
            "recent_orders": recent_orders,
            "top_products": top_products,
            "low_stock_items": low_stock_items,
            "monthly_sales_trend": monthly_trend[::-1],  # Reverse to show oldest first
        })
