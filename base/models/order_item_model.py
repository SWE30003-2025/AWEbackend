from django.db import models
from .order_model import OrderModel
from .product_model import ProductModel

class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(OrderModel, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(ProductModel, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase

    def __str__(self):
        return f"{self.quantity} x {self.product.name} for Order {self.order.pk}"

    class Meta:
        db_table = "order_item"  
