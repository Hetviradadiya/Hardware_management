from django.urls import path,include
from rest_framework.routers import DefaultRouter
from inventory_app.views import DashboardsView
from pricemanagement_app.views import ProductViewSet, ProductPriceViewSet, DealerViewSet, BulkProductCreateAPIView

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='products')
router.register(r'product-prices', ProductPriceViewSet, basename='product-prices')
router.register(r'dealers', DealerViewSet, basename='dealers')

urlpatterns = router.urls

urlpatterns = [
    path('product/', DashboardsView.as_view(template_name="products.html"), name='product'),
    path('api/', include(router.urls)),
    path('api/product-create/', BulkProductCreateAPIView.as_view(), name='bulk-products-create'),
    path('api/product-create/<int:pk>/', BulkProductCreateAPIView.as_view(), name='bulk-products-update'),
]