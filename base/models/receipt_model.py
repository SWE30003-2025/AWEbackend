from django.db import models
from .payment_model import PaymentModel

class ReceiptModel(models.Model):
    id = models.AutoField(primary_key=True)
    payment = models.OneToOneField(PaymentModel, on_delete=models.CASCADE, related_name="receipt")
    receipt_number = models.CharField(max_length=50, unique=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Receipt {self.receipt_number} for Payment {self.payment.transaction_id}"
    
    @property
    def order(self):
        """Get the related order through payment -> invoice -> order"""
        return self.payment.invoice.order
    
    @property
    def user(self):
        """Get the user who made the payment"""
        return self.payment.user
    
    class Meta:
        db_table = "receipt" 
