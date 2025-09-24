from django.urls import path,include
from pricemanagement_app.views import ProductViewset
from rest_framework.routers import DefaultRouter
from inventory_app.views import DashboardsView
router=DefaultRouter()
router.register('products', ProductViewset, basename='products')

urlpatterns = [
    path('product/', DashboardsView.as_view(template_name="products.html"), name='product'),
    path('api/', include(router.urls)),
]