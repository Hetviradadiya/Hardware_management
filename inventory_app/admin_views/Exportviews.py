from django.http import HttpResponse
from openpyxl import Workbook
from inventory_app.models import Order
from inventory_app.serializers import OrderSerializer 
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

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

from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from inventory_app.models import Order, Customer
from inventory_app.serializers import OrderSerializer
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
# from weasyprint import HTML
# from django.template.loader import render_to_string

@permission_classes([IsAuthenticated])
def export_customer_orders_pdf(request, pk):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    orders = Order.objects.filter(customer_id=pk)
    if start_date and end_date:
        orders = orders.filter(order_date__date__range=[start_date, end_date])

    customer = Customer.objects.get(id=pk)
    serializer = OrderSerializer(orders, many=True)
    orders_data = serializer.data
    #Calculate grand total here in Python
    total_sum = sum(float(order["final_amount"]) for order in orders_data)

    # Render HTML template
    template_path = "pdf_templates/customer_orders.html"
    context = {
        "customer": customer,
        "orders": orders_data,
        "start_date": start_date,
        "end_date": end_date,
        "total_sum": total_sum,
    }

    template = get_template(template_path)
    html = template.render(context)

    # Generate PDF from HTML
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename=customer_{pk}_orders.pdf"
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)
    return response

    # html_string = render_to_string("pdf_templates/customer_orders.html", context)
    # response = HttpResponse(content_type="application/pdf")
    # response["Content-Disposition"] = f"attachment; filename=customer_{pk}_orders.pdf"
    # HTML(string=html_string).write_pdf(response)
    # return response


# # views.py
# from django.http import HttpResponse
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.pagesizes import A4
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.enums import TA_CENTER
# from inventory_app.models import Order, Customer
# from inventory_app.serializers import OrderSerializer
# from django.utils.dateparse import parse_date

# @permission_classes([IsAuthenticated])
# def export_customer_orders_pdf(request, pk):
#     start_date = request.GET.get("start_date")
#     end_date = request.GET.get("end_date")

#     orders = Order.objects.filter(customer_id=pk)
#     if start_date and end_date:
#         orders = orders.filter(order_date__date__range=[start_date, end_date])

#     customer = Customer.objects.get(id=pk)
#     serializer = OrderSerializer(orders, many=True)
#     orders_data = serializer.data

#     # Setup response
#     response = HttpResponse(content_type="application/pdf")
#     response["Content-Disposition"] = f"attachment; filename=customer_{pk}_orders.pdf"

#     # PDF setup
#     doc = SimpleDocTemplate(response, pagesize=A4)
#     elements = []
#     styles = getSampleStyleSheet()

#     # Custom center style
#     center_style = ParagraphStyle(
#         name="Center", parent=styles["Normal"], alignment=TA_CENTER, fontSize=12
#     )
#     center_heading = ParagraphStyle(
#         name="CenterHeading",
#         parent=styles["Heading1"],
#         alignment=TA_CENTER
#     )


#     # Title
#     elements.append(Paragraph("Customer Orders Report", center_heading))
#     elements.append(Spacer(1, 12))

#     # Customer Info (centered)
#     elements.append(Paragraph(f"Customer Name: {customer.name}", center_style))
#     elements.append(Paragraph(f"Phone No: {customer.phone}", center_style))

#     elements.append(Spacer(1, 12))

#     # Table headers
#     data = [["ID", "Order Date", "Total Amount", "Discount", "Final Amount",
#              "Product", "Quantity", "Price at Sale"]]

#     # Fill rows
#     for order in orders_data:
#         order_items = order["order_items"]

#         if order_items:  # if order has items
#             # First row: include order-level fields + first item
#             first_item = order_items[0]
#             data.append([
#                 order["id"],
#                 order["order_date"],
#                 f"₹ {order['total_amount']}",
#                 f"{order['order_discount']}%" if order["is_percentage"] else f"₹ {order['order_discount']}",
#                 f"₹ {order['final_amount']}",
#                 first_item.get("product_name", ""),
#                 first_item.get("quantity", ""),
#                 first_item.get("price_at_sale", ""),
#             ])
#             # Other rows: leave order fields blank
#             for item in order_items[1:]:
#                 data.append([
#                     "", "", "", "", "",
#                     item.get("product_name", ""),
#                     item.get("quantity", ""),
#                     item.get("price_at_sale", ""),
#                 ])
#         else:
#             # Order with no items
#             data.append([
#                 order["id"],
#                 order["order_date"],
#                 f"₹ {order['total_amount']}",
#                 f"{order['order_discount']}%" if order["is_percentage"] else f"₹ {order['order_discount']}",
#                 f"₹ {order['final_amount']}",
#                 "-", "-", "-"
#             ])

#     # Create table
#     table = Table(data, repeatRows=1, colWidths=[40, 100, 70, 60, 70, 100, 50, 70])
#     table.setStyle(TableStyle([
#         ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
#         ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
#         ("ALIGN", (0, 0), (-1, -1), "CENTER"),
#         ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
#         ("FONTSIZE", (0, 0), (-1, 0), 10),
#         ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
#         ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
#     ]))

#     elements.append(table)
#     doc.build(elements)

#     return response
