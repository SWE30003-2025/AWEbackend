from django.db import models
from .shopping_cart_model import ShoppingCartModel
from .product_model import ProductModel

class CartItemModel(models.Model):
    id = models.AutoField(primary_key=True)
    cart = models.ForeignKey(ShoppingCartModel, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.cart.user.username}'s cart"

    @property
    def subtotal(self):
        """Calculate subtotal for this cart item"""
        return self.product.price * self.quantity

    class Meta:
        db_table = "cart_item"
        unique_together = ('cart', 'product')  # Prevent duplicate products in same cart 
