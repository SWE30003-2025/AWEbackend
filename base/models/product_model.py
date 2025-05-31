import uuid
from django.db import models

class ProductModel(models.Model):
    id          = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    name        = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    price       = models.DecimalField(max_digits=10, decimal_places=2)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "product"
