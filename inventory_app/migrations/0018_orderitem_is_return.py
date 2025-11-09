# Generated migration for OrderItem is_return field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_app', '0017_order_return_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='is_return',
            field=models.BooleanField(default=False, help_text='Mark if this item has been returned'),
        ),
    ]