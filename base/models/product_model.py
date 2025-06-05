import uuid
from django.db import models

class ProductModel(models.Model):
    id          = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    name        = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    price       = models.DecimalField(max_digits=10, decimal_places=2)
    stock       = models.PositiveIntegerField(default=0)
    is_active   = models.BooleanField(default=True)
    category    = models.ForeignKey(
        "base.CategoryModel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="category_id",
        related_name="products"
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "product"
