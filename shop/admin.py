from django.contrib import admin
from .models import CustomUser, Product, Cart, Order

admin.site.register(CustomUser)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(Order)
