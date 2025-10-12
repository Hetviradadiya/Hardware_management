import nested_admin
from django.contrib import admin
from .models import Product, ProductPrice, Dealer, ProductSize


# ----------------- Dealer Inline (Nested) -----------------
class DealerInline(nested_admin.NestedTabularInline):
    model = Dealer
    extra = 1
    fields = (
        "dlr_name", "slol", "purchase_date",
        "purchase_price", "purchase_discount", "purchase_discount_price",
        "purchase_tax", "purchase_tax_price",
        "purchase_box", "purchase_box_discount",
        "purchase_box_discount_price", "purchase_box_tax", "purchase_box_tax_price",
    )


# ----------------- ProductPrice Inline (Nested) -----------------
class ProductPriceInline(nested_admin.NestedTabularInline):
    model = ProductPrice
    extra = 1
    inlines = [DealerInline]
    fields = (
        "payment_type", "price", "discount", "discount_price",
        "tax", "tax_price", "box", "box_discount",
        "box_discount_price", "box_tax", "box_tax_price"
    )

@admin.register(ProductPrice)
class ProductPriceAdmin(admin.ModelAdmin):
    list_display = ("product", "payment_type", "price", "discount", "tax")
    search_fields = ("product__name", "payment_type")

class ProductSizeInline(nested_admin.NestedTabularInline):
    model = ProductSize
    extra = 1
    fields = ['size', 'code', 'hsn', 'mrp']
    
# ----------------- Product Admin (Nested) -----------------
@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    list_display = ("id", "photo", "name")
    search_fields = ("name",)
    inlines = [ProductPriceInline]

    class Media:
        css = {"all": ("admin/css/custom_admin.css",)}
