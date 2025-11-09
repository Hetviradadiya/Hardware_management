from django.http import HttpResponse
from openpyxl import Workbook
from inventory_app.models import *
from inventory_app.serializers import OrderSerializer 
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.template.loader import get_template
from django.http import HttpResponse
from datetime import datetime
import pdfkit

@permission_classes([IsAuthenticated])
def export_customer_orders_excel(request, pk):
    # Fetch orders for this customer
    orders = Order.objects.filter(customer_id=pk)

    # Serialize orders
    serializer = OrderSerializer(orders, many=True)
    orders_data = serializer.data

    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Orders"

    # Define headers
    headers = [
        "Order ID", "Customer ID", "Customer Name", "Order Date","Product",
        "Total Amount", "Discount", "Is %", "Final Amount",
         "Quantity", "Price at Sale"
    ]
    ws.append(headers)

    # Fill rows
    for order in orders_data:
        if order["order_items"]:  # If order has items
            for item in order["order_items"]:
                ws.append([
                    order["id"],
                    order["customer"],
                    order["customer_name"],
                    order["order_date"],
                    item.get("product_name", ""),
                    order["total_amount"],
                    order["order_discount"],
                    "Yes" if order["is_percentage"] else "No",
                    order["final_amount"],
                    item.get("quantity", ""),
                    item.get("price_at_sale", ""),
                ])
        else:
            # Handle orders without items (still include order row)
            ws.append([
                order["id"],
                order["customer"],
                order["customer_name"],
                order["order_date"],
                order["total_amount"],
                order["order_discount"],
                "Yes" if order["is_percentage"] else "No",
                order["final_amount"],
                "", "", "",  # No product info
            ])

    # Return as downloadable Excel
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename=customer_{pk}_orders.xlsx'
    wb.save(response)
    return response

@permission_classes([IsAuthenticated])
def export_customer_orders_pdf(request, pk):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    orders = Order.objects.filter(customer_id=pk)
    if start_date and end_date:
        orders = orders.filter(order_date__date__range=[start_date, end_date])

    customer = Customer.objects.get(id=pk)
    
    #Calculate grand total here in Python  
    total_sum = sum(order.total_amount for order in orders)

    # Render HTML template - use queryset directly for proper date formatting
    template_path = "pdf_templates/customer_orders.html"
    context = {
        "customer": customer,
        "orders": orders,  # Use queryset instead of serialized data
        "start_date": start_date,
        "end_date": end_date,
        "total_sum": total_sum,
    }

    template = get_template(template_path)
    html = template.render(context)

    # Generate PDF using pdfkit
    path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"  
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"customer_{pk}_orders_{current_time}.pdf"

    pdf = pdfkit.from_string(html, False, configuration=config)

    # Return response
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response

@permission_classes([IsAuthenticated])
def export_supplier_purchases_pdf(request, pk):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    purchases = Purchase.objects.filter(supplier_id=pk)
    if start_date and end_date:
        purchases = purchases.filter(date__range=[start_date, end_date])

    supplier = Supplier.objects.get(id=pk)
    total_sum = sum(p.total_price for p in purchases)

    template_path = "pdf_templates/supplier_purchases.html"
    context = {
        "supplier": supplier,
        "purchases": purchases,
        "start_date": start_date,
        "end_date": end_date,
        "total_sum": total_sum,
    }

    template = get_template(template_path)
    html = template.render(context)
    
    # Generate PDF using pdfkit
    path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe" 
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"supplier_{pk}_purchases_{current_time}.pdf"

    pdf = pdfkit.from_string(html, False, configuration=config)

    # Return response
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
