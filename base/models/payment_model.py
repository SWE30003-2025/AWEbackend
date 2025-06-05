from django.db import models

from .user_model import UserModel
from .invoice_model import InvoiceModel

from base.enums import PAYMENT_STATUS

class PaymentModel(models.Model):
    id = models.AutoField(primary_key=True)
    invoice = models.ForeignKey(InvoiceModel, on_delete=models.CASCADE, related_name="payments")
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name.title()) for status in PAYMENT_STATUS],
        default=PAYMENT_STATUS.PENDING.value
    )
    transaction_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Payment {self.transaction_id} for Invoice {self.invoice.invoice_number}"
    
    def mark_as_completed(self):
        """Mark payment as completed"""
        from django.utils import timezone
        self.status = PAYMENT_STATUS.COMPLETED.value
        self.completed_at = timezone.now()
        self.save()
    
    class Meta:
        db_table = "payment" 
