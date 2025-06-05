import re

from django.db import models

class CategoryModel(models.Model):
    id = models.CharField(
        max_length=255,
        editable=False,
        unique=True,
        primary_key=True
    )
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        # Remove all whitespace and lowercase:
        # "My Category Name" → "mycategoryname"
        stripped = re.sub(r"\s+", "", self.name)
        self.id = stripped.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "category"
