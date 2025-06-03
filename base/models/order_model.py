from django.db import models
from .user_model import UserModel 

class OrderModel(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=32, default="processing")  # e.g., processing, shipped, delivered, cancelled

    def __str__(self):
        return f"Order {self.pk} by {self.user.username}"

    class Meta:
        db_table = "order"  
