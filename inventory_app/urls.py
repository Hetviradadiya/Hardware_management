
from .views import DashboardsView, ChangePasswordAPIView
from django.urls import path,include
from inventory_app.admin_views.DashboadView import DashboardStatsAPIView, DashboardDataAPIView
from inventory_app.admin_views.CategoryViews import CategoryView
from inventory_app.admin_views.ProductViews import ProductView,ProductVariantView
from inventory_app.admin_views.PurchaseViews import PurchaseViewSet, purchase_products
from inventory_app.admin_views.SuppliersViews import SupplierView, supplier_purchases
from inventory_app.admin_views.CustomerViews import CustomerView
from inventory_app.admin_views.inventoryView import InventoryViewSet
from inventory_app.admin_views.POSViews import CartViewSet, place_order,bill_page
from inventory_app.admin_views.CustomerOrderView import customer_orders,order_detail_api
from inventory_app.admin_views.Exportviews import export_customer_orders_excel, export_customer_orders_pdf, export_supplier_purchases_pdf, print_customer_orders_pdf, print_supplier_purchases_pdf
from inventory_app.admin_views.SalesView import SalesListAPI
from inventory_app.admin_views.UserManagementViews import UserManagementViewSet, RoleManagementViewSet
from inventory_app.admin_views.OrderManagementViews import OrderManagementViewSet
from inventory_app.admin_views.ReturnsManagementViews import ReturnsManagementViewSet
from inventory_app.admin_views.OrderItemManagementViews import OrderItemManagementViewSet

from rest_framework.routers import DefaultRouter

router=DefaultRouter()
router.register('categories', CategoryView, basename='categories')
router.register('suppliers', SupplierView, basename='suppliers')
router.register('customers', CustomerView, basename='customers')
router.register('products', ProductView, basename='products')
router.register('product-variants', ProductVariantView, basename='product-variants')
router.register('purchases', PurchaseViewSet, basename='purchases')
router.register('inventories', InventoryViewSet, basename='inventories')
router.register('cart', CartViewSet, basename='cart')
router.register('users', UserManagementViewSet, basename='users')
router.register('roles', RoleManagementViewSet, basename='roles')
router.register('order-management', OrderManagementViewSet, basename='order-management')
router.register('returns-management', ReturnsManagementViewSet, basename='returns-management')
router.register('order-items', OrderItemManagementViewSet, basename='order-items')

urlpatterns = [

    path('dashboard/', DashboardsView.as_view(template_name="dashboard.html"), name='dashboard'),

    # urls.py

    path('category-list/', DashboardsView.as_view(template_name="category_list.html"), name='category-list'),
    path('category/add/', DashboardsView.as_view(template_name="category.html"), name='category-add'),
    path('category/edit/<int:id>/', DashboardsView.as_view(template_name="category.html"), name='category-edit'),
    path('category/detail/<int:id>/', DashboardsView.as_view(template_name="category.html"), name='category-detail'),

    path('product-list/', DashboardsView.as_view(template_name="product_list.html"), name='product-list'),
    path('product/add/', DashboardsView.as_view(template_name="product.html"), name='product-add'),
    path('product/edit/<int:id>/', DashboardsView.as_view(template_name="product.html"), name='product-edit'),
    path('product/detail/<int:id>/', DashboardsView.as_view(template_name="product.html"), name='product-detail'),

    path('supplier-list/', DashboardsView.as_view(template_name="supplier_list.html"), name='supplier-list'),
    path('supplier/add/', DashboardsView.as_view(template_name="supplier.html"), name='supplier-add'),
    path('supplier/edit/<int:id>/', DashboardsView.as_view(template_name="supplier.html"), name='supplier-edit'),
    path('supplier/detail/<int:id>/', DashboardsView.as_view(template_name="supplier.html"), name='supplier-detail'),

    path('customer-list/', DashboardsView.as_view(template_name="customer_list.html"), name='customer-list'),
    path('customer/add/', DashboardsView.as_view(template_name="customer.html"), name='customer-add'),
    path('customer/edit/<int:id>/', DashboardsView.as_view(template_name="customer.html"), name='customer-edit'),
    path('customer/detail/<int:id>/', DashboardsView.as_view(template_name="customer.html"), name='customer-detail'),

    path('purchase-list/', DashboardsView.as_view(template_name="purchase_list.html"), name='purchase-list'),
    path('purchase/add/', DashboardsView.as_view(template_name="purchase_add.html"), name='purchase-add'),
    path('purchase/edit/<int:id>/', DashboardsView.as_view(template_name="purchase_edit_view.html"), name='purchase-edit'),
    path('purchase/detail/<int:id>/', DashboardsView.as_view(template_name="purchase_edit_view.html"), name='purchase-detail'),

    path('inventory-list/', DashboardsView.as_view(template_name="inventory_list.html"), name='inventory-list'),
    
    path('sales-list/', DashboardsView.as_view(template_name="sales_list.html"), name='sales-list'),

    path('pos/', DashboardsView.as_view(template_name="pos.html"), name='pos'),
    path('cart_view/', DashboardsView.as_view(template_name="cart.html"), name='cart-view'),
    
    path('customer-orders/<int:pk>/', DashboardsView.as_view(template_name="customer_orders.html"), name='customer-orders'),
    path('customer-orders/<int:pk>/customer-order-detail/<int:id>/', DashboardsView.as_view(template_name="customer_order_detail.html"), name= 'customer-order-detail'),

    # Settings Page
    path('settings/', DashboardsView.as_view(template_name="settings.html"), name='settings'),
    
    # Order Management and Returns
    path('orders-list/', DashboardsView.as_view(template_name="orders_list.html"), name='orders-list'),
    path('order/<int:order_id>/edit/', DashboardsView.as_view(template_name="order_edit.html"), name='order-edit'),
    path('order/<int:order_id>/', DashboardsView.as_view(template_name="order.html"), name='order-detail'),
    path('returns-management/', DashboardsView.as_view(template_name="returns_management.html"), name='returns-management'),

    # API Endpoints
    path("admin_api/customer-orders/<int:pk>/export_excel/", export_customer_orders_excel, name="export_customer-order_excel"),
    path("admin_api/customer-orders/<int:pk>/export_pdf/", export_customer_orders_pdf, name="customer_orders_pdf"),
    path("admin_api/customer-orders/<int:pk>/print_pdf/", print_customer_orders_pdf, name="print_customer_orders_pdf"),
    
    path('supplier-purchases/<int:pk>/', DashboardsView.as_view(template_name="supplier_purchses.html"), name='supplier_purchses'),
    path("admin_api/supplier-purchases/<int:pk>/export_pdf/", export_supplier_purchases_pdf, name="supplier_purchases_pdf"),
    path("admin_api/supplier-purchases/<int:pk>/print_pdf/", print_supplier_purchases_pdf, name="print_supplier_purchases_pdf"),
    
    path('place_order/', place_order, name='place_order'),
    path('bill/<int:order_id>/', bill_page, name='bill_page'),
    
    path('admin_api/', include(router.urls)),

    path('admin_api/purchase-products/', purchase_products, name='purchase-products'),
    path('admin_api/orders/<int:pk>/', customer_orders, name='orders'),
    path("admin_api/order/<int:id>/", order_detail_api, name="order-detail-api"),
    
    path('admin_api/supplier-purchases/<int:pk>/', supplier_purchases, name='supplier_purchases'),
    
    path("admin_api/hardware-dashboard-stats/", DashboardStatsAPIView.as_view(), name="hardware-dashboard-stats"),
    path("admin_api/hardware-dashboard-data/", DashboardDataAPIView.as_view(), name="hardware-dashboard-data"),

    path('admin_api/sales/', SalesListAPI.as_view(), name='sales_list_api'),
    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
]
