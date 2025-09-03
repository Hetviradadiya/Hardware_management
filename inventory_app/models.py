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

    def __str__(self):
        return f"{self.product.name} - {self.size}"


# ---------- INVENTORY ----------
class Inventory(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

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
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.variant} x {self.quantity}"


# ---------- ORDER ----------
class Order(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="orders", null=True, blank=True
    )
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    order_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  
    is_percentage = models.BooleanField(default=True)  # True if discount is %

    def calculate_total(self):
        """
        Recalculate total considering items & order-level discount.
        """
        subtotal = sum(item.subtotal() for item in self.items.all())

        if self.is_percentage:
            discount_value = (subtotal * self.order_discount) / 100
        else:
            discount_value = self.order_discount

        return subtotal - discount_value

    def __str__(self):
        return f"Order #{self.id} - {self.customer.name if self.customer else 'No Customer'}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)

    item_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_percentage = models.BooleanField(default=True)  # True if discount is %

    def subtotal(self):
        """
        Subtotal considering product-wise discount.
        """
        total = self.quantity * self.price_at_sale

        if self.is_percentage:
            discount_value = (total * self.item_discount) / 100
        else:
            discount_value = self.item_discount

        return total - discount_value

    def __str__(self):
        return f"{self.variant} x {self.quantity}"
    
# ---------- SALES ----------
class Sale(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    sale_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # NEW

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        total_profit = 0
        for item in self.order.items.all():
            # Get last purchase price for this variant (or average cost)
            purchase = Purchase.objects.filter(variant=item.variant).order_by('-date').first()
            if purchase:
                purchase_cost = (purchase.purchase_price * item.quantity) - purchase.discount
                gst_amount = (purchase_cost * purchase.gst) / 100
                final_cost = purchase_cost + gst_amount

                revenue = item.quantity * item.price_at_sale
                total_profit += revenue - final_cost

            # Deduct stock from Inventory
            inventory_item = Inventory.objects.get(variant=item.variant)
            inventory_item.quantity -= item.quantity
            inventory_item.save()

        self.profit = total_profit
        super().save(update_fields=["profit"])

    def __str__(self):
        return f"Sale for Order #{self.order.id}"
