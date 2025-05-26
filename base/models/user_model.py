from django.contrib.auth.models import AbstractBaseUser
from django.db import models
import uuid

class UserModel(AbstractBaseUser):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    username = models.CharField(max_length=255, unique=True)

    USERNAME_FIELD = "username"

    def __str__(self):
        return f"{self.username}"

    class Meta:
        db_table = "user"  # Overwrites the default table name
