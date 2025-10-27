from django.contrib import admin
from .models import *

# -------------------- Admin Models --------------------

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)

@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    list_display = ('username','full_name', 'email', 'mobile', 'role', 'is_staff', 'is_superuser')
    list_filter = ('username','is_staff', 'is_superuser', 'role')
    search_fields = ('username','full_name', 'email', 'mobile')
    readonly_fields = ('date_joined',)

@admin.register(LoginRecord)
class LoginRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'login_time', 'user_agent']
    search_fields = ['user__email', 'ip_address', 'user_agent']
    list_filter = ['login_time']
    
    def user(self, obj):
        return obj.user.full_name if obj.user else "Unknown User"
    
    user.short_description = 'User'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'address')
    search_fields = ('name', 'phone', 'email')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'address')
    search_fields = ('name', 'phone', 'email')

class ProductVariantInline(admin.TabularInline):  # Or admin.StackedInline for bigger form
    model = ProductVariant
    extra = 1  # Number of empty rows to display by default
    min_num = 1  # At least one variant required
    fields = ('size', 'price', 'discount', 'gst', 'total_price')
    readonly_fields = ('total_price',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)
    inlines = [ProductVariantInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'price', 'discount', 'gst', 'total_price')
    list_filter = ('product',)
    search_fields = ('product__name', 'size')
    readonly_fields = ('total_price',)

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('variant', 'quantity')
    search_fields = ('variant__product__name', 'variant__size')


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'variant', 'quantity', 'purchase_price', 'date')
    list_filter = ('supplier', 'date')
    search_fields = ('supplier__name', 'variant__product__name')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('variant', 'quantity','price', 'date_added')
    search_fields = ('variant__product__name',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'order_date', 'total_amount')
    list_filter = ('order_date',)
    search_fields = ('customer',)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'variant', 'quantity', 'price_at_sale')
    search_fields = ('order__customer_name', 'variant__product__name')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('order', 'sale_date', 'total_amount')
    list_filter = ('sale_date',)
    search_fields = ('order__customer_name',)