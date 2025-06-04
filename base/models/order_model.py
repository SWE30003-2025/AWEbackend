from django.db import models
from .user_model import UserModel 

class OrderModel(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=32, default="processing")  # e.g., processing, shipped, delivered, cancelled
    
    # Shipping address fields
    shipping_full_name = models.CharField(max_length=255)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)

    def __str__(self):
        return f"Order {self.pk} by {self.user.username}"

    @property
    def total(self):
        """Calculate total price of all items in this order"""
        return sum(item.price * item.quantity for item in self.items.all())

    class Meta:
        db_table = "order"  
