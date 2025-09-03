import json
from rest_framework import serializers
from .models import *


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class ProductVariantSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = ProductVariant
        fields = ["id", "size", "price", "total_price", "product_name"]
        read_only_fields = ["total_price"]


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, required=False)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "category", "category_name", "photo", "variants"]

    def _get_variants_data(self):
        """Helper to get variants as a list of dicts even if sent as JSON string."""
        request = self.context.get("request")
        variants_data = request.data.get("variants", [])
        if isinstance(variants_data, str):
            try:
                variants_data = json.loads(variants_data)
            except json.JSONDecodeError:
                variants_data = []
        return variants_data

    def create(self, validated_data):
        variants_data = self._get_variants_data()
        product = Product.objects.create(
            name=validated_data.get("name"),
            category=validated_data.get("category"),
            photo=validated_data.get("photo")
        )

        for variant in variants_data:
            ProductVariant.objects.create(product=product, **variant)

        return product

    def update(self, instance, validated_data):
        variants_data = self._get_variants_data()

        instance.name = validated_data.get("name", instance.name)
        instance.category = validated_data.get("category", instance.category)
        if "photo" in validated_data:
            instance.photo = validated_data.get("photo", instance.photo)
        instance.save()

        # Handle variant updates
        existing_ids = [v.get("id") for v in variants_data if v.get("id")]
        ProductVariant.objects.filter(product=instance).exclude(id__in=existing_ids).delete()

        for variant in variants_data:
            if variant.get("id"):  # Update existing variant
                var_obj = ProductVariant.objects.get(id=variant["id"], product=instance)
                for key, value in variant.items():
                    setattr(var_obj, key, value)
                var_obj.save()
            else:  # Create new variant
                ProductVariant.objects.create(product=instance, **variant)

        return instance

# class PurchaseSerializer(serializers.ModelSerializer):
#     supplier_name = serializers.SerializerMethodField()
#     variant_name = serializers.SerializerMethodField()

#     def get_supplier_name(self, obj):
#         return obj.supplier.name if obj.supplier else "None"
    
#     def get_variant_name(self,obj):
#         return obj.variant.product.name if obj.variant else "None"

#     class Meta:
#         model = Purchase
#         fields = ['id', 'supplier', 'supplier_name', 'variant','variant_name','quantity', 'purchase_price', 'date']

class PurchaseSerializer(serializers.ModelSerializer):
    supplier = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.all())
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    category_id = serializers.IntegerField(source='variant.product.category.id', read_only=True)
    category_name = serializers.CharField(source='variant.product.category.name', read_only=True)
    variant_size = serializers.CharField(source='variant.size', read_only=True)
    variant_price = serializers.DecimalField(source='variant.price', max_digits=10, decimal_places=2, read_only=True)
    product_photo = serializers.ImageField(source='variant.product.photo', read_only=True)

    class Meta:
        model = Purchase
        fields = [
            'id', 'supplier_name','supplier', 'variant','product_name', 'category_id', 'category_name',
            'variant_size', 'variant_price', 'product_photo',
            'quantity', 'purchase_price', 'discount', 'gst', 'total_price', 'date'
        ]

class InventorySerializer(serializers.ModelSerializer):
    variant_name = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()

    def get_variant_name(self, obj):
        return obj.variant.product.name if obj.variant else "None"
    
    def get_size(self, obj):
        return obj.variant.size if obj.variant else "None"
    
    class Meta:
        model = Inventory
        fields = ['id', 'variant', 'variant_name','size', 'quantity']

class InventoryVariantSerializer(serializers.ModelSerializer):
    size = serializers.CharField(source="variant.size", default="", allow_null=True)
    price = serializers.DecimalField(source="variant.price", max_digits=10, decimal_places=2, default=0.00, allow_null=True)
    product_name = serializers.CharField(source="variant.product.name", read_only=True, default="")
    product_photo = serializers.ImageField(source="variant.product.photo", read_only=True, default=None)
    category_id = serializers.IntegerField(source="variant.product.category.id", read_only=True, default=0)
    category_name = serializers.CharField(source="variant.product.category.name", read_only=True, default="")

    class Meta:
        model = Inventory
        fields = [
            "id",
            "variant",
            "size",
            "price",
            "quantity",
            "product_name",
            "product_photo",
            "category_id",
            "category_name",
        ]

class CartSerializer(serializers.ModelSerializer):
    variant_name = serializers.CharField(source="variant.product.name", read_only=True)
    variant_size = serializers.CharField(source="variant.size", read_only=True)
    variant_price = serializers.DecimalField(source="variant.price", max_digits=10, decimal_places=2, read_only=True)
    variant_photo = serializers.SerializerMethodField()
    class Meta:
        model = Cart
        fields = ["id", "variant", "variant_name","variant_photo", "variant_size", "variant_price", "quantity", "date_added"]

    def get_variant_photo(self, obj):
        request = self.context.get("request")
        photo = obj.variant.product.photo
        if photo:
            return request.build_absolute_uri(photo.url)
        return None
    
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    product_size = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "product_name","product_size", "quantity", "price_at_sale", "total_price"]

    def get_total_price(self, obj):
        return obj.quantity * obj.price_at_sale
    
    def get_product_name(self,obj):
        return obj.variant.product.name if obj.variant else "None"
    
    def get_product_size(self,obj):
        return obj.variant.size if obj.variant else "None"