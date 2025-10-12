from rest_framework import serializers
from .models import Product, ProductPrice, Dealer, ProductSize

class DealerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dealer
        exclude = ('product_price',)  # exclude FK, will set in create()

class ProductPriceSerializer(serializers.ModelSerializer):
    dealers = DealerSerializer(many=True)

    class Meta:
        model = ProductPrice
        exclude = ('product',)  # exclude FK, will set in create()

    def create(self, validated_data):
        dealers_data = validated_data.pop('dealers', [])
        product_price = ProductPrice.objects.create(**validated_data)
        for dealer_data in dealers_data:
            Dealer.objects.create(product_price=product_price, **dealer_data)
        return product_price
    
# -------------------- PRODUCT SIZE SERIALIZER --------------------
class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    prices = ProductPriceSerializer(many=True, read_only=False)
    sizes = ProductSizeSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = '__all__'

    def create(self, validated_data):
        prices_data = validated_data.pop('prices', [])
        sizes_data = validated_data.pop('sizes', [])
        product = Product.objects.create(**validated_data)

        # Create Product Prices & Dealers
        for price_data in prices_data:
            dealers_data = price_data.pop('dealers', [])
            product_price = ProductPrice.objects.create(product=product, **price_data)
            for dealer_data in dealers_data:
                Dealer.objects.create(product_price=product_price, **dealer_data)

        # Create Product Sizes
        for size_data in sizes_data:
            ProductSize.objects.create(product=product, **size_data)

        return product

    def update(self, instance, validated_data):
        prices_data = validated_data.pop('prices', [])
        sizes_data = validated_data.pop('sizes', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update Prices
        for price_data in prices_data:
            price_id = price_data.get('id', None)
            dealers_data = price_data.pop('dealers', [])
            if price_id:
                price_obj = ProductPrice.objects.get(id=price_id, product=instance)
                for attr, value in price_data.items():
                    setattr(price_obj, attr, value)
                price_obj.save()
            else:
                price_obj = ProductPrice.objects.create(product=instance, **price_data)
            # Update Dealers
            for dealer_data in dealers_data:
                dealer_id = dealer_data.get('id', None)
                if dealer_id:
                    dealer_obj = Dealer.objects.get(id=dealer_id, product_price=price_obj)
                    for attr, value in dealer_data.items():
                        setattr(dealer_obj, attr, value)
                    dealer_obj.save()
                else:
                    Dealer.objects.create(product_price=price_obj, **dealer_data)

        # Update Sizes
        for size_data in sizes_data:
            size_id = size_data.get('id', None)
            if size_id:
                size_obj = ProductSize.objects.get(id=size_id, product=instance)
                for attr, value in size_data.items():
                    setattr(size_obj, attr, value)
                size_obj.save()
            else:
                ProductSize.objects.create(product=instance, **size_data)

        return instance