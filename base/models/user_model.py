from django.contrib.auth.models import AbstractBaseUser
from django.db import models
import uuid
from base.enums import ROLE

class UserModel(AbstractBaseUser):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    firstName = models.CharField(max_length=255)
    lastName = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    password = models.CharField(max_length=255)
    role = models.CharField(
        max_length=32,
        choices=[(role.value, role.name.title()) for role in ROLE],
        default=ROLE.CUSTOMER.value,
    )

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "firstName", "lastName"]

    def __str__(self):
        return f"{self.username}"

    class Meta:
        db_table = "user"  # Overwrites the default table name
