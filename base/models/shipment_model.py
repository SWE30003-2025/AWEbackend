from django.db import models

from .order_model import OrderModel

from base.enums import SHIPMENT_STATUS

class ShipmentModel(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.OneToOneField(OrderModel, on_delete=models.CASCADE, related_name="shipment")
    tracking_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(
        max_length=32,
        choices=[(status.value, status.name.title()) for status in SHIPMENT_STATUS],
        default=SHIPMENT_STATUS.PENDING.value
    )
    carrier = models.CharField(max_length=100, default="AWE Express")
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Shipment {self.tracking_number} for Order {self.order.id}"
    
    class Meta:
        db_table = "shipment" 
