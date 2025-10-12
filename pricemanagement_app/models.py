from django.db import models

# -------------------- PRODUCT --------------------
class Product(models.Model):
    photo = models.ImageField(upload_to="products/", blank=True, null=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name
    
class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sizes")
    size = models.CharField(max_length=50, blank=True, null=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    hsn = models.CharField(max_length=50, blank=True, null=True)
    mrp = models.FloatField(default=0,blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} {(self.size)}"


# -------------------- PAYMENT TYPE --------------------
PAYMENT_TYPE_CHOICES = [
    ("cash", "Cash"),
    ("bill", "Bill"),
    ("sale_cash", "Sale Cash"),
    ("sale_bill", "Sale Bill"),
    ("frd_cash", "Frd Cash"),
    ("frd_bill", "Frd Bill"),
]


# -------------------- PRODUCT PRICE --------------------
class ProductPrice(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="prices")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)

    # --- Selling Price Fields ---
    price = models.FloatField(default=0)
    discount = models.FloatField(default=0)
    discount_price = models.FloatField(default=0)
    tax = models.FloatField(default=0)
    tax_price = models.FloatField(default=0)

    box = models.FloatField(default=0)
    box_discount = models.FloatField(default=0)
    box_discount_price = models.FloatField(default=0)
    box_tax = models.FloatField(default=0)
    box_tax_price = models.FloatField(default=0)

    def __str__(self):
        return f"{self.product.name}"

    @property
    def final_price(self):
        subtotal = self.price - (self.price * self.discount / 100)
        return subtotal + (subtotal * self.tax / 100)


# -------------------- DEALER --------------------
class Dealer(models.Model):
    product_price = models.ForeignKey(ProductPrice, on_delete=models.CASCADE, related_name="dealers")

    # --- Dealer Info ---
    dlr_name = models.CharField(max_length=100,blank=True, null=True)
    slol = models.CharField(max_length=100, blank=True, null=True)

    # --- Dealer-specific Purchase Fields ---
    purchase_date = models.DateField(blank=True, null=True)
    purchase_price = models.FloatField(default=0)
    purchase_discount = models.FloatField(default=0)
    purchase_discount_price = models.FloatField(default=0)
    purchase_tax = models.FloatField(default=0)
    purchase_tax_price = models.FloatField(default=0)

    purchase_box = models.FloatField(default=0)
    purchase_box_discount = models.FloatField(default=0)
    purchase_box_discount_price = models.FloatField(default=0)
    purchase_box_tax = models.FloatField(default=0)
    purchase_box_tax_price = models.FloatField(default=0)

    def __str__(self):
        return f"{self.dlr_name} ({self.slol}) - {self.product_price.product.name}"

    @property
    def final_purchase_price(self):
        subtotal = self.purchase_price - (self.purchase_price * self.purchase_discount / 100)
        return subtotal + (subtotal * self.purchase_tax / 100)