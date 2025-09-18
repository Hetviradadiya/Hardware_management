from django.urls import path,include
from pricemanagement_app.views import ProductViewset
from rest_framework.routers import DefaultRouter

router=DefaultRouter()
router.register('products', ProductViewset, basename='products')

urlpatterns = [
    path('api/', include(router.urls)),
]