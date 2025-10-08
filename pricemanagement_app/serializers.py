from rest_framework import serializers
from .models import Product, ProductPrice, Dealer

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

class ProductSerializer(serializers.ModelSerializer):
    prices = ProductPriceSerializer(many=True)

    class Meta:
        model = Product
        fields = '__all__'

    def create(self, validated_data):
        prices_data = validated_data.pop('prices', [])
        product = Product.objects.create(**validated_data)
        for price_data in prices_data:
            dealers_data = price_data.pop('dealers', [])
            product_price = ProductPrice.objects.create(product=product, **price_data)
            for dealer_data in dealers_data:
                Dealer.objects.create(product_price=product_price, **dealer_data)
        return product