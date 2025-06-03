from django.db import models
from base.models import UserModel, ProductModel  # Adjust this import if needed

class OrderModel(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=32, default="processing")  # e.g., processing, shipped, delivered, cancelled

    def __str__(self):
        return f"Order {self.pk} by {self.user.username}"

    @property
    def total(self):
        # Dynamically calculate total from all order items
        return float(sum(item.price * item.quantity for item in self.items.all()))

class OrderItem(models.Model):
    order = models.ForeignKey(OrderModel, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(ProductModel, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase

    def __str__(self):
        return f"{self.quantity} x {self.product.name} for Order {self.order.pk}"
