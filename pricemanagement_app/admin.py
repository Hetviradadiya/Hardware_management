from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id", "name", "hsn_code", "size", "pcs_size","mrp",
        "purchase_price", "purchase_discount", "purchase_tax",
        "sale_price", "sale_discount", "sale_tax",
        "current_purchase_total", "current_sale_total",
        "created_at", "updated_at",
    )
    search_fields = ("name", "hsn_code", "size","pcs_size")
    list_filter = ("created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at", "current_purchase_total", "current_sale_total")

    fieldsets = (
        ("Basic Info", {
            "fields": ("photo", "name", "hsn_code", "size","pcs_size", "mrp")
        }),
        ("Purchase Details", {
            "fields": ("purchase_price", "purchase_discount", "purchase_tax",
                       "purchase_price_100", "purchase_tax_100", "current_purchase_total")
        }),
        ("Sale Details", {
            "fields": ("sale_price", "sale_discount", "sale_tax",
                       "sale_price_100", "sale_tax_100", "current_sale_total")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    def current_purchase_total(self, obj):
        """Safe calculation of purchase final price (with discount + tax)."""
        if not obj.purchase_price:
            return None
        discount_amt = (obj.purchase_price * (obj.purchase_discount or 0)) / 100
        subtotal = obj.purchase_price - discount_amt
        return subtotal + (subtotal * (obj.purchase_tax or 0) / 100)
    current_purchase_total.short_description = "Purchase Final Price"

    def current_sale_total(self, obj):
        """Safe calculation of sale final price (with discount + tax)."""
        if not obj.sale_price:
            return None
        discount_amt = (obj.sale_price * (obj.sale_discount or 0)) / 100
        subtotal = obj.sale_price - discount_amt
        return subtotal + (subtotal * (obj.sale_tax or 0) / 100)
    current_sale_total.short_description = "Sale Final Price"
