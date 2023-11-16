from django.contrib import admin
from .models import Product, Review, Profile, CartItem, Notification

# Register your models here.
admin.site.register(Product)
admin.site.register(Review)
admin.site.register(Profile)
admin.site.register(CartItem)
admin.site.register(Notification)