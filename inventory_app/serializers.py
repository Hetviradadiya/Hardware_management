import json
from rest_framework import serializers
from .models import *
from decimal import Decimal


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
    discount_price = serializers.SerializerMethodField()
    gst_amount = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    is_percentage = serializers.BooleanField(default=True)
    item_discount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst = serializers.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        model = Cart
        fields = [
            "id", "variant", "variant_name", "variant_photo", "variant_size", "variant_price","price",
            "quantity", "date_added", "item_discount", "is_percentage", "gst",
            "discount_price", "gst_amount", "total_price"
        ]

    def get_variant_photo(self, obj):
        request = self.context.get("request")
        photo = obj.variant.product.photo
        if photo:
            return request.build_absolute_uri(photo.url)
        return None

    def get_discount_price(self, obj):
        base_price = obj.price or obj.variant.price
        price = base_price * obj.quantity
        if obj.is_percentage:
            return round(price * obj.item_discount / 100, 2)
        return round(obj.item_discount, 2)

    def get_gst_amount(self, obj):
        base_price = obj.price or obj.variant.price
        price_after_discount = base_price * obj.quantity - self.get_discount_price(obj)
        return round(price_after_discount * obj.gst / 100, 2)

    def get_total_price(self, obj):
        base_price = obj.price or obj.variant.price
        price = base_price * obj.quantity
        discount = self.get_discount_price(obj)
        gst_amount = self.get_gst_amount(obj)
        return round(price - discount + gst_amount, 2)
    

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    product_size = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    discount_price = serializers.SerializerMethodField()
    gst_amount = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "variant",
            "product_name",
            "product_size",
            "quantity",
            "price_at_sale",
            "item_discount",
            "is_percentage",
            "gst",
            "is_return",
            "discount_price",
            "gst_amount",
            "total_price",
        ]

    def get_product_name(self, obj):
        return obj.variant.product.name if obj.variant else None

    def get_product_size(self, obj):
        return obj.variant.size if obj.variant else None

    def get_total_price(self, obj):
        return obj.total_price()

    def get_discount_price(self, obj):
        return obj.discount_price()

    def get_gst_amount(self, obj):
        return obj.gst_amount()

class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    order_items = OrderItemSerializer(source="items", many=True, read_only=True)
    order_date = serializers.SerializerMethodField()
    
    def get_order_date(self, obj):
        """Convert order date to local timezone for proper display"""
        from django.utils import timezone
        if obj.order_date:
            # Convert to local timezone
            local_time = timezone.localtime(obj.order_date)
            # Return in ISO format which JavaScript can properly parse
            return local_time.isoformat()
        return None
    
    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "customer_name",
            "order_date",
            "status",
            "subtotal",
            "total_item_discount",
            "order_discount",
            "is_percentage",
            "total_discount",
            "total_gst",
            "total_amount",
            "pay_type",
            "is_paid",
            "pod_number",
            "paid_amount",
            "return_amount",
            "note",
            "order_items",
        ]

# class OrderSerializer(serializers.ModelSerializer):
#     customer_name = serializers.CharField(source="customer.name", read_only=True)
#     order_items = OrderItemSerializer(source="items", many=True, read_only=True)
#     subtotal = serializers.SerializerMethodField()
#     discount_value = serializers.SerializerMethodField()
#     final_amount = serializers.SerializerMethodField()
#     order_date = serializers.DateTimeField(format="%Y-%m-%d", read_only=True)

#     class Meta:
#         model = Order
#         fields = [
#             "id",
#             "customer",
#             "customer_name",
#             "order_date",
#             "total_amount",
#             "order_discount",
#             "is_percentage",
#             "pay_type",
#             "is_paid",
#             "pod_number",
#             "paid_amount",
#             "note",
#             "order_items",
#             "subtotal",
#             "discount_value",
#             "final_amount",
#             "total_gst",
#         ]

#     def get_subtotal(self, obj):
#         return obj.subtotal

#     def get_discount_value(self, obj):
#         subtotal = sum([(item.price_at_sale * item.quantity) - getattr(item, "item_discount", 0)
#                     for item in obj.items.all()])
#         return subtotal - obj.total_amount

#     def get_final_amount(self, obj):
#         return obj.total_amount


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile management in settings"""
    role_name = serializers.CharField(source='role.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = UserAccount
        fields = [
            'id', 'username', 'full_name', 'email', 'mobile',
            'is_active', 'is_staff', 'is_superuser', 'date_joined',
            'address_line', 'city', 'state', 'country', 'postal_code',
            'role', 'role_name', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['date_joined', 'created_by']
        
    def validate_email(self, value):
        """Validate email uniqueness excluding current user"""
        if self.instance and self.instance.email == value:
            return value
        if UserAccount.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
        
    def validate_mobile(self, value):
        """Validate mobile uniqueness excluding current user"""
        if self.instance and self.instance.mobile == value:
            return value
        if UserAccount.objects.filter(mobile=value).exists():
            raise serializers.ValidationError("A user with this mobile number already exists.")
        return value


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users"""
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = UserAccount
        fields = [
            'username', 'full_name', 'email', 'mobile', 'password', 'confirm_password',
            'is_active', 'is_staff', 'address_line', 'city', 'state', 'country', 
            'postal_code', 'role'
        ]
        
    def validate(self, data):
        """Validate password confirmation"""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
        
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        user = UserAccount.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for role management"""
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']


class ReturnItemSerializer(serializers.ModelSerializer):
    """Serializer for return items"""
    order_item_product_name = serializers.CharField(source="order_item.variant.product.name", read_only=True)
    order_item_variant_size = serializers.CharField(source="order_item.variant.size", read_only=True)
    order_item_price = serializers.DecimalField(source="order_item.price_at_sale", max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ReturnItem
        fields = [
            'id', 'order_item', 'return_quantity', 'condition', 
            'refund_per_unit', 'total_refund',
            'order_item_product_name', 'order_item_variant_size', 'order_item_price'
        ]


class OrderReturnSerializer(serializers.ModelSerializer):
    """Serializer for order returns"""
    return_items = ReturnItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="original_order.customer.name", read_only=True)
    order_id = serializers.IntegerField(source="original_order.id", read_only=True)
    processed_by_name = serializers.CharField(source="processed_by.full_name", read_only=True)
    
    class Meta:
        model = OrderReturn
        fields = [
            'id', 'original_order', 'order_id', 'customer_name', 
            'return_date', 'status', 'reason', 'notes',
            'total_return_amount', 'refund_amount', 'processing_fee',
            'processed_by', 'processed_by_name', 'processed_at',
            'return_items'
        ]
    