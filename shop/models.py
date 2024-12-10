from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    pass

from django.db import models

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Food'),
        ('clothes', 'Clothes'),
        ('electronics', 'Electronics'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='products/')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='food')

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


    @classmethod
    def get_cart(cls, user):
        return cls.objects.filter(user=user)

    @classmethod
    def remove_from_cart(cls, user, product_id):
        item = cls.objects.get(user=user, product_id=product_id)
        item.delete()

class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date_ordered = models.DateTimeField(auto_now_add=True)
    is_returned = models.BooleanField(default=False)
    address = models.TextField(null=True, blank=True)  # New field
    phone_number = models.CharField(max_length=15, null=True, blank=True)  # New field
    pincode = models.CharField(max_length=10, null=True, blank=True)  # New field
    is_paid = models.BooleanField(default=False)
    rating = models.PositiveIntegerField(
        null=True, blank=True,default=None,
        choices=[(i, str(i)) for i in range(1, 6)]
    )
    
    @staticmethod
    def get_average_rating(product):
        orders_with_rating = Order.objects.filter(product=product, rating__isnull=False)
        if orders_with_rating.exists():
            return orders_with_rating.aggregate(average_rating=models.Avg('rating'))['average_rating']
        return None

