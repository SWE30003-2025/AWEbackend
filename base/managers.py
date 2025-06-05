import uuid
from datetime import timedelta

from django.utils import timezone

from base.models import ProductModel, ShipmentModel
from base.enums import SHIPMENT_STATUS

class InventoryManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InventoryManager, cls).__new__(cls)
        return cls._instance

    def get_stock(self, product_id):
        product = ProductModel.objects.get(pk=product_id)
        return getattr(product, 'stock', None)

    def set_stock(self, product_id, quantity):
        product = ProductModel.objects.get(pk=product_id)
        product.stock = quantity
        product.save()
        return product.stock

    def adjust_stock(self, product_id, amount):
        product = ProductModel.objects.get(pk=product_id)
        if not hasattr(product, 'stock'):
            product.stock = 0
        product.stock += amount
        product.save()
        return product.stock

    def all_inventory(self):
        return [(p, getattr(p, 'stock', None)) for p in ProductModel.objects.all()] 


class ShipmentManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ShipmentManager, cls).__new__(cls)
        return cls._instance

    def create_shipment(self, order):
        """Create a new shipment for an order"""
        tracking_number = f"AWE{uuid.uuid4().hex[:8].upper()}"
        
        estimated_delivery = timezone.now() + timedelta(days=5)
        
        # Create shipment with PENDING status
        shipment = ShipmentModel.objects.create(
            order=order,
            tracking_number=tracking_number,
            status=SHIPMENT_STATUS.PENDING.value,
            estimated_delivery=estimated_delivery
        )
        
        print(f"Shipment Manager notified! Created shipment {tracking_number} for Order {order.id}")
        print(f"Shipment status updates will be handled manually by shipment managers.")
        
        return shipment
    
    def update_shipment_status(self, shipment_id, new_status):
        """Update the status of a shipment (for manual updates by authorized users)"""
        try:
            shipment = ShipmentModel.objects.get(id=shipment_id)
            old_status = shipment.status
            shipment.status = new_status
            
            # If status is delivered, set actual delivery time and update order status
            if new_status == SHIPMENT_STATUS.DELIVERED.value:
                shipment.actual_delivery = timezone.now()
                order = shipment.order
                order.status = "delivered"
                order.save()
                print(f"Order {order.id} marked as delivered!")
            
            shipment.save()
            print(f"Shipment {shipment.tracking_number} status updated from {old_status} to: {new_status}")
            
        except ShipmentModel.DoesNotExist:
            print(f"Shipment with id {shipment_id} not found")
    
    def get_shipment_status(self, tracking_number):
        """Get the current status of a shipment by tracking number"""
        try:
            shipment = ShipmentModel.objects.get(tracking_number=tracking_number)
            return {
                'tracking_number': shipment.tracking_number,
                'status': shipment.status,
                'carrier': shipment.carrier,
                'estimated_delivery': shipment.estimated_delivery,
                'actual_delivery': shipment.actual_delivery,
                'order_id': shipment.order.id
            }
        except ShipmentModel.DoesNotExist:
            return None 
