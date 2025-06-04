from base.models.product_model import ProductModel
import uuid
import threading
from datetime import datetime, timedelta
from django.utils import timezone
from base.models import ShipmentModel, OrderModel
from base.enums.shipment_status import SHIPMENT_STATUS

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
        """Create a new shipment for an order and start the shipping process"""
        # Generate unique tracking number
        tracking_number = f"AWE{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate estimated delivery (3-7 business days)
        estimated_delivery = timezone.now() + timedelta(days=5)
        
        # Create shipment
        shipment = ShipmentModel.objects.create(
            order=order,
            tracking_number=tracking_number,
            status=SHIPMENT_STATUS.PENDING.value,
            estimated_delivery=estimated_delivery
        )
        
        print(f"📦 Shipment Manager notified! Created shipment {tracking_number} for Order {order.id}")
        
        # Start the fake shipping process
        self._start_shipping_timer(shipment)
        
        return shipment
    
    def _start_shipping_timer(self, shipment):
        """Start a timer to simulate the shipping process"""
        def shipping_process():
            # Stage 1: Processing (immediate)
            self.update_shipment_status(shipment.id, SHIPMENT_STATUS.PROCESSING.value)
            
            # Stage 2: Shipped (after 5 seconds)
            threading.Timer(5.0, lambda: self.update_shipment_status(shipment.id, SHIPMENT_STATUS.SHIPPED.value)).start()
            
            # Stage 3: In Transit (after 10 seconds)
            threading.Timer(10.0, lambda: self.update_shipment_status(shipment.id, SHIPMENT_STATUS.IN_TRANSIT.value)).start()
            
            # Stage 4: Out for Delivery (after 15 seconds)
            threading.Timer(15.0, lambda: self.update_shipment_status(shipment.id, SHIPMENT_STATUS.OUT_FOR_DELIVERY.value)).start()
            
            # Stage 5: Delivered (after 20 seconds)
            threading.Timer(20.0, lambda: self._complete_delivery(shipment.id)).start()
        
        # Start the shipping process in a separate thread
        threading.Thread(target=shipping_process, daemon=True).start()
    
    def update_shipment_status(self, shipment_id, new_status):
        """Update the status of a shipment"""
        try:
            shipment = ShipmentModel.objects.get(id=shipment_id)
            shipment.status = new_status
            shipment.save()
            print(f"🚚 Shipment {shipment.tracking_number} status updated to: {new_status}")
        except ShipmentModel.DoesNotExist:
            print(f"❌ Shipment with id {shipment_id} not found")
    
    def _complete_delivery(self, shipment_id):
        """Complete the delivery process"""
        try:
            shipment = ShipmentModel.objects.get(id=shipment_id)
            shipment.status = SHIPMENT_STATUS.DELIVERED.value
            shipment.actual_delivery = timezone.now()
            shipment.save()
            
            # Update order status to delivered
            order = shipment.order
            order.status = "delivered"
            order.save()
            
            print(f"✅ Shipment {shipment.tracking_number} delivered successfully!")
        except ShipmentModel.DoesNotExist:
            print(f"❌ Shipment with id {shipment_id} not found")
    
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
