import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

from base.enums import ROLE

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username field must be set")
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("role", ROLE.ADMIN.value)
        return self.create_user(username, email, password, **extra_fields)

class UserModel(AbstractBaseUser):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    firstName = models.CharField(max_length=255)
    lastName = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(
        max_length=32,
        choices=[(role.value, role.name.title()) for role in ROLE],
        default=ROLE.CUSTOMER.value,
    )
    wallet = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Customer's wallet balance (only used for customer role)"
    )

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "firstName", "lastName"]

    def __str__(self):
        return f"{self.username}"

    @property
    def wallet_balance(self):
        """Returns wallet balance for customers only"""
        if self.role == ROLE.CUSTOMER.value:
            return self.wallet
        return None

    class Meta:
        db_table = "user"  # Overwrites the default table name
