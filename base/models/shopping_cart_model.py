from django.db import models

from .user_model import UserModel 

class ShoppingCartModel(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(UserModel, on_delete=models.CASCADE, related_name="shopping_cart")

    def __str__(self):
        return f"Shopping Cart for {self.user.username}"

    @property
    def total(self):
        """Calculate total price of all items in the cart"""
        return sum(item.product.price * item.quantity for item in self.items.all())

    @property
    def total_items(self):
        """Get total number of items in the cart"""
        return sum(item.quantity for item in self.items.all())

    def clear(self):
        """Remove all items from the cart"""
        self.items.all().delete()

    class Meta:
        db_table = "shopping_cart" 
