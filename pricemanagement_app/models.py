from django.db import models
from django.core.exceptions import ValidationError


class Product(models.Model):
    hsn_code = models.CharField(max_length=20, blank=True, null=True)
    photo = models.ImageField(upload_to="products/", blank=True, null=True)
    name = models.CharField(max_length=255)
    size = models.CharField(max_length=50, blank=True, null=True)
    pcs_size = models.CharField(max_length=50, blank=True, null=True)
    mrp = models.FloatField()

    purchase_price = models.FloatField()
    purchase_discount = models.FloatField(default=0)
    purchase_discount_price = models.FloatField(default=0)  
    purchase_tax = models.FloatField(default=0)
    purchase_tax_price = models.FloatField(default=0) 
    final_purchase_price = models.FloatField(blank=True,null=True)   

    purchase_price_100 = models.FloatField(blank=True, null=True)
    purchase_discount_100 = models.FloatField(default=0)
    purchase_discount_price_100 = models.FloatField(default=0)
    purchase_tax_100 = models.FloatField(default=0)
    purchase_tax_price_100 = models.FloatField(default=0)

    sale_price = models.FloatField()
    sale_discount = models.FloatField(default=0)
    sale_discount_price = models.FloatField(default=0)    
    sale_tax = models.FloatField(default=0)
    sale_tax_price = models.FloatField(default=0)
    final_sale_price = models.FloatField(blank=True,null=True)   

    sale_price_100 = models.FloatField(blank=True, null=True)
    sale_discount_100 = models.FloatField(default=0)
    sale_discount_price_100 = models.FloatField(default=0)
    sale_tax_100 = models.FloatField(default=0)
    sale_tax_price_100 = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        purchase_discount_amount = (self.purchase_price * self.purchase_discount) / 100
        purchase_subtotal = self.purchase_price - purchase_discount_amount
        purchase_total = purchase_subtotal + (purchase_subtotal * self.purchase_tax / 100)

        sale_discount_amount = (self.sale_price * self.sale_discount) / 100
        sale_subtotal = self.sale_price - sale_discount_amount
        sale_total = sale_subtotal + (sale_subtotal * self.sale_tax / 100)

        if self.purchase_price < 0 or self.sale_price < 0:
            raise ValidationError("Price cannot be negative.")

        if self.purchase_discount < 0 or self.sale_discount < 0:
            raise ValidationError("Discount cannot be negative.")

        if self.purchase_tax < 0 or self.sale_tax < 0:
            raise ValidationError("Tax cannot be negative.")

        if sale_total < purchase_total:
            raise ValidationError(
                f"Invalid pricing: Sale total ({sale_total}) should not be less than purchase total ({purchase_total})."
            )

    def __str__(self):
        return self.name
