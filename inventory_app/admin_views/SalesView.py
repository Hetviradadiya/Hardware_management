from rest_framework.views import APIView
from rest_framework.response import Response
from inventory_app.models import Sale
from django.utils.dateparse import parse_date
from inventory_app.pagination import ListPagination
from django.db.models import Q

class SalesListAPI(APIView):
    pagination_class = ListPagination

    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        search = request.GET.get('search', '').strip()

        sales = Sale.objects.select_related('order', 'order__customer').order_by('-sale_date')

        # 🔹 Apply date filtering
        if start_date and end_date:
            start = parse_date(start_date)
            end = parse_date(end_date)
            if start and end:
                sales = sales.filter(sale_date__date__range=(start, end))
                
        if search:
            sales = sales.filter(
                Q(order__id__icontains=search) |
                Q(order__customer__name__icontains=search) |
                Q(order__pay_type__icontains=search)
            )

        paginator = self.pagination_class()
        paginated_sales = paginator.paginate_queryset(sales, request, view=self)

        data = []
        for s in paginated_sales:
            data.append({
                "sale_date": s.sale_date.strftime("%d %b %Y, %I:%M %p"),
                "order_id": s.order.id,
                "customer_name": s.order.customer.name if s.order.customer else "Walk-in",
                "pay_type": s.order.pay_type,
                "total_amount": str(s.total_amount),
                "paid_amount": str(s.paid_amount),
                "profit": str(s.profit),
            })

        return paginator.get_paginated_response(data)

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from inventory_app.models import Sale
# from django.utils.dateparse import parse_date

# class SalesListAPI(APIView):
#     def get(self, request):
#         start_date = request.GET.get('start_date')
#         end_date = request.GET.get('end_date')

#         sales = Sale.objects.select_related('order', 'order__customer').order_by('-sale_date')

#         # 🔹 Apply date filtering if both dates are provided
#         if start_date and end_date:
#             start = parse_date(start_date)
#             end = parse_date(end_date)
#             if start and end:
#                 sales = sales.filter(sale_date__date__range=(start, end))

#         data = []
#         for s in sales:
#             data.append({
#                 "sale_date": s.sale_date.strftime("%d %b %Y, %I:%M %p"),
#                 "order_id": s.order.id,
#                 "customer_name": s.order.customer.name if s.order.customer else "Walk-in",
#                 "pay_type": s.order.pay_type,
#                 "total_amount": str(s.total_amount),
#                 "paid_amount": str(s.paid_amount),
#                 "profit": str(s.profit),
#             })
#         return Response(data)
