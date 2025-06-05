from django.db import models
from django.utils import timezone

from .order_model import OrderModel

from base.enums import INVOICE_STATUS

class InvoiceModel(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.OneToOneField(OrderModel, on_delete=models.CASCADE, related_name="invoice")
    invoice_number = models.CharField(max_length=50, unique=True)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name.title()) for status in INVOICE_STATUS],
        default=INVOICE_STATUS.PENDING.value
    )
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number} for Order {self.order.id}"
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        return self.status == INVOICE_STATUS.PENDING.value and timezone.now() > self.due_date
    
    def mark_as_paid(self):
        """Mark invoice as paid"""
        self.status = INVOICE_STATUS.PAID.value
        self.save()
    
    class Meta:
        db_table = "invoice" 
