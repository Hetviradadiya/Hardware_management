from django.db import models
from django.contrib.auth.models import User,AbstractUser,Group,Permission,BaseUserManager
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone

# Create your models here.
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class AccountManager(BaseUserManager):
    use_in_migrations = True
 
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # This hashes the password
        user.save(using=self._db)
        return user
 
    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)
 
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', Role.objects.get_or_create(name='Admin')[0])
 
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
 
        return self._create_user(email, password, **extra_fields)
 
class Role(BaseModel):     
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
 
    def __str__(self):
        return self.name
 
 
class Module(BaseModel):   
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
 
    def __str__(self):
        return self.name
   
 
class UserAccount(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=20, unique=True, blank=True, null=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(verbose_name="email_address", max_length=255, unique=True)
    mobile = models.CharField(max_length=20,unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    address_line = models.TextField(blank=True, null=True)
    city = models.CharField(blank=True, null=True, max_length=255)
    state = models.CharField(blank=True, null=True, max_length=255)
    country = models.CharField(blank=True, null=True, max_length=255)
    postal_code = models.CharField(blank=True, null=True, max_length=255)
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL)
    created_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='created_users'
    )
   
    objects = AccountManager()
 
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['full_name','mobile']
 
    def __str__(self):
        return self.full_name
 
    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

class LoginRecord(models.Model):
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    login_time = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.ip_address} at {self.login_time}"


from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


# ---------- CATEGORY ----------
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# ---------- SUPPLIER ----------
class Supplier(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Customer(models.Model):
    name = models.CharField(max_length=255,blank=True, null=True)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    pending_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    advance_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

# ---------- PRODUCT ----------
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products")
    name = models.CharField(max_length=255)
    photo = models.ImageField(upload_to="products/", blank=True, null=True)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    size = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Discount in %")
    gst = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="GST in %")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        price_after_discount = self.price - (self.price * self.discount / 100)
        gst_amount = price_after_discount * self.gst / 100
        self.total_price = price_after_discount + gst_amount
        super().save(*args, **kwargs)
        
        Inventory.objects.get_or_create(
            variant=self,
            defaults={'quantity': 0}
        )

    def __str__(self):
        return f"{self.product.name} - {self.size}"


# ---------- INVENTORY ----------
class Inventory(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ('variant',)

    def __str__(self):
        return f"{self.variant} - {self.quantity} pcs"


# ---------- PURCHASE ----------
class Purchase(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    gst = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  
    total_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0.00)
    date = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        base_price = self.quantity * self.purchase_price

        discounted_price = base_price - self.discount if self.discount else base_price

        # Apply GST (assuming gst is %)
        gst_amount = (discounted_price * self.gst) / 100
        self.total_price = discounted_price + gst_amount
        
        super().save(*args, **kwargs)
        # Update Inventory
        inventory_item, created = Inventory.objects.get_or_create(
            variant=self.variant,
            defaults={'quantity': self.quantity}
        )
        if not created:
            inventory_item.quantity += self.quantity
            inventory_item.save()

    def __str__(self):
        return f"Purchase of {self.variant} from {self.supplier}"

# ---------- CART ----------
class Cart(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    date_added = models.DateTimeField(auto_now_add=True)
    item_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_percentage = models.BooleanField(default=True)  
    gst = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  

    def discount_price(self):
        total = self.variant.price * self.quantity
        if self.is_percentage:
            return (total * self.item_discount) / Decimal(100)
        return self.item_discount

    def gst_amount(self):
        return ((self.variant.price * self.quantity - self.discount_price()) * self.gst) / Decimal(100)

    def total_price(self):
        return (self.variant.price * self.quantity) - self.discount_price() + self.gst_amount()

    def __str__(self):
        return f"{self.variant} x {self.quantity}"


# ---------- ORDER ----------
class Order(models.Model):
    PAYMENT_TYPE_CHOICES = (
        ('cash', 'cash'),
        ('online', 'online'),
        ('card', 'card'),
    )
    
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="orders", null=True, blank=True
    )
    order_date = models.DateTimeField(auto_now_add=True)
    # totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)         # 💡 sum of qty * price
    total_item_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    order_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_percentage = models.BooleanField(default=True)
    total_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)   # 💡 item + order discount
    total_gst = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)     # 💡 grand total after discounts + gst
 
    is_percentage = models.BooleanField(default=True)  
    pay_type = models.CharField(max_length=200, choices=PAYMENT_TYPE_CHOICES, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    note = models.TextField(blank=True, null=True)
    pod_number = models.CharField(max_length=255, blank=True, null=True)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # def subtotal(self):
    #     return sum(item.total_price() for item in self.items.all())

    # def discount_value(self):
    #     subtotal = self.subtotal()
    #     if self.is_percentage:
    #         return (subtotal * self.order_discount) / Decimal(100)
    #     return self.order_discount

    # def get_total_amount(self):
    #     return self.subtotal() - self.discount_value()

    def __str__(self):
        return f"Order #{self.id} - {self.customer.name if self.customer else 'No Customer'}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)

    item_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_percentage = models.BooleanField(default=True)  # True if discount is %
    gst = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def discount_price(self):
        total = self.price_at_sale * self.quantity
        if self.is_percentage:
            return (total * self.item_discount) / Decimal(100)
        return self.item_discount

    def gst_amount(self):
        return ((self.price_at_sale * self.quantity - self.discount_price()) * self.gst) / Decimal(100)

    def total_price(self):
        return (self.price_at_sale * self.quantity) - self.discount_price() + self.gst_amount()


    def __str__(self):
        return f"{self.variant} x {self.quantity}"
    
# ---------- SALES ----------
class Sale(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    sale_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    paid_amount = models. DecimalField(max_digits=20, decimal_places=2, default=0.0)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        total_profit = Decimal("0.00")
        order_discount = getattr(self.order, "order_discount", Decimal("0.00"))
        order_total_before_discount = sum(
            [(item.price_at_sale * item.quantity) - getattr(item, "item_discount", 0) 
             for item in self.order.items.all()]
        )

        for item in self.order.items.all():
            # Get last purchase for cost price
            purchase = Purchase.objects.filter(variant=item.variant).order_by('-date').first()
            if purchase:
                base_cost = purchase.purchase_price * item.quantity
                cost_after_discount = base_cost - purchase.discount
                cost_with_gst = cost_after_discount + ((cost_after_discount * purchase.gst) / 100)
            else:
                cost_with_gst = Decimal("0.00")

            # Revenue side
            revenue = (item.price_at_sale * item.quantity) - getattr(item, "item_discount", 0)

            # Apply proportional order discount
            if order_discount and order_total_before_discount > 0:
                share = revenue / order_total_before_discount
                revenue -= (share * order_discount)

            # Calculate profit
            profit_per_item = revenue - cost_with_gst
            total_profit += profit_per_item

            # Deduct stock
            inventory_item = Inventory.objects.get(variant=item.variant)
            inventory_item.quantity -= item.quantity
            inventory_item.save()

        self.profit = total_profit
        super().save(update_fields=["profit"])

    def __str__(self):
        return f"Sale for Order #{self.order.id}"
