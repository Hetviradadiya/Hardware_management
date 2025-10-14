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
        exclude = ('product_size',)  # exclude FK, will set in create()

    def create(self, validated_data):
        dealers_data = validated_data.pop('dealers', [])
        product_price = ProductPrice.objects.create(**validated_data)
        for dealer_data in dealers_data:
            Dealer.objects.create(product_price=product_price, **dealer_data)
        return product_price
    
# -------------------- PRODUCT SIZE SERIALIZER --------------------
class ProductSizeSerializer(serializers.ModelSerializer):
    prices = ProductPriceSerializer(many=True, required=False)

    class Meta:
        model = ProductSize
        exclude = ('product',)  # exclude FK, will set in create()

    def create(self, validated_data):
        prices_data = validated_data.pop('prices', [])
        product_size = ProductSize.objects.create(**validated_data)
        
        # Create Product Prices & Dealers for this size
        for price_data in prices_data:
            dealers_data = price_data.pop('dealers', [])
            product_price = ProductPrice.objects.create(product_size=product_size, **price_data)
            for dealer_data in dealers_data:
                Dealer.objects.create(product_price=product_price, **dealer_data)
        
        return product_size

class ProductSerializer(serializers.ModelSerializer):
    sizes = ProductSizeSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = '__all__'

    def create(self, validated_data):
        sizes_data = validated_data.pop('sizes', [])
        product = Product.objects.create(**validated_data)

        # Create Product Sizes with their Prices & Dealers
        for size_data in sizes_data:
            prices_data = size_data.pop('prices', [])
            product_size = ProductSize.objects.create(product=product, **size_data)
            
            # Create Product Prices & Dealers for this size
            for price_data in prices_data:
                dealers_data = price_data.pop('dealers', [])
                product_price = ProductPrice.objects.create(product_size=product_size, **price_data)
                for dealer_data in dealers_data:
                    Dealer.objects.create(product_price=product_price, **dealer_data)

        return product

    def update(self, instance, validated_data):
        sizes_data = validated_data.pop('sizes', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update Sizes with their Prices & Dealers
        for size_data in sizes_data:
            size_id = size_data.get('id', None)
            prices_data = size_data.pop('prices', [])
            
            if size_id:
                size_obj = ProductSize.objects.get(id=size_id, product=instance)
                for attr, value in size_data.items():
                    setattr(size_obj, attr, value)
                size_obj.save()
            else:
                size_obj = ProductSize.objects.create(product=instance, **size_data)
            
            # Update Prices for this size
            for price_data in prices_data:
                price_id = price_data.get('id', None)
                dealers_data = price_data.pop('dealers', [])
                
                if price_id:
                    price_obj = ProductPrice.objects.get(id=price_id, product_size=size_obj)
                    for attr, value in price_data.items():
                        setattr(price_obj, attr, value)
                    price_obj.save()
                else:
                    price_obj = ProductPrice.objects.create(product_size=size_obj, **price_data)
                
                # Update Dealers for this price
                for dealer_data in dealers_data:
                    dealer_id = dealer_data.get('id', None)
                    if dealer_id:
                        dealer_obj = Dealer.objects.get(id=dealer_id, product_price=price_obj)
                        for attr, value in dealer_data.items():
                            setattr(dealer_obj, attr, value)
                        dealer_obj.save()
                    else:
                        Dealer.objects.create(product_price=price_obj, **dealer_data)

        return instance