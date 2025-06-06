import uuid
from datetime import timedelta, datetime

from django.utils import timezone
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from django.db.models.expressions import OuterRef, Subquery

from base.models import ProductModel, ShipmentModel, OrderModel, OrderItemModel
from base.enums import SHIPMENT_STATUS

class InventoryManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InventoryManager, cls).__new__(cls)
        return cls._instance

    def get_stock(self, product_id):
        product = ProductModel.objects.get(pk=product_id)
        return getattr(product, "stock", None)

    def set_stock(self, product_id, quantity):
        product = ProductModel.objects.get(pk=product_id)
        product.stock = quantity
        product.save()
        return product.stock

    def adjust_stock(self, product_id, amount):
        product = ProductModel.objects.get(pk=product_id)
        if not hasattr(product, "stock"):
            product.stock = 0
        product.stock += amount
        product.save()
        return product.stock

    def all_inventory(self):
        return [(p, getattr(p, "stock", None)) for p in ProductModel.objects.all()] 


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
                "tracking_number": shipment.tracking_number,
                "status": shipment.status,
                "carrier": shipment.carrier,
                "estimated_delivery": shipment.estimated_delivery,
                "actual_delivery": shipment.actual_delivery,
                "order_id": shipment.order.id,
            }
        except ShipmentModel.DoesNotExist:
            return None 

class StatisticsManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StatisticsManager, cls).__new__(cls)
        return cls._instance

    def get_sales_by_period(self, period_type, start_date=None, end_date=None):
        """
        Get sales statistics for a specific period type
        period_type: 'day', 'week', 'month', 'year', or 'ytd' (year to date)
        """
        # If no end date specified, use current date
        if not end_date:
            end_date = timezone.now()
        
        # If no start date specified, determine based on period type
        if not start_date:
            if period_type == "ytd":
                start_date = datetime(end_date.year, 1, 1, tzinfo=end_date.tzinfo)
            else:
                # Default to last 30 days if no period specified
                start_date = end_date - timedelta(days=30)

        orders = OrderModel.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            status="delivered"
        )

        trunc_func = {
            "day": TruncDate("created_at"),
            "week": TruncWeek("created_at"),
            "month": TruncMonth("created_at"),
            "year": TruncYear("created_at"),
            "ytd": TruncDate("created_at")
        }.get(period_type, TruncDate("created_at"))

        if period_type == "day":
            period_trunc = TruncDate("order__created_at")
        elif period_type == "week":
            period_trunc = TruncWeek("order__created_at")
        elif period_type == "month":
            period_trunc = TruncMonth("order__created_at")
        elif period_type == "year":
            period_trunc = TruncYear("order__created_at")
        else:  # ytd or default
            period_trunc = TruncDate("order__created_at")

        sales_by_period = OrderItemModel.objects.filter(
            order__created_at__gte=start_date,
            order__created_at__lte=end_date,
            order__status="delivered"
        ).annotate(
            period=period_trunc,
            item_total=ExpressionWrapper(
                F("quantity") * F("price"),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        ).values("period").annotate(
            total_orders=Count("order__id", distinct=True),
            total_sales=Sum("item_total")
        ).order_by("period")

        return sales_by_period

    def get_top_selling_products(self, start_date=None, end_date=None, limit=10):
        """Get top selling products within a date range"""
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        return OrderItemModel.objects.filter(
            order__created_at__gte=start_date,
            order__created_at__lte=end_date,
            order__status="delivered"
        ).values(
            "product__id",
            "product__name",
            "product__category__name"
        ).annotate(
            total_quantity=Sum("quantity"),
            total_revenue=Sum(
                ExpressionWrapper(
                    F("quantity") * F("price"),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            )
        ).annotate(
            product_id=F("product__id"),
            product_name=F("product__name"),
            category_name=F("product__category__name")
        ).values(
            "product_id",
            "product_name",
            "category_name",
            "total_quantity",
            "total_revenue"
        ).order_by("-total_quantity")[:limit]

    def get_sales_summary(self, start_date=None, end_date=None):
        """Get overall sales summary for a date range"""
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        orders = OrderModel.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            status="delivered"
        )

        total_revenue = OrderItemModel.objects.filter(
            order__in=orders
        ).aggregate(
            total=Sum(
                ExpressionWrapper(
                    F("quantity") * F("price"),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            )
        )["total"] or 0

        total_orders = orders.count()
        total_items_sold = OrderItemModel.objects.filter(
            order__in=orders
        ).aggregate(
            total=Sum("quantity")
        )["total"] or 0

        return {
            "period_start": start_date,
            "period_end": end_date,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_items_sold": total_items_sold,
            "average_order_value": total_revenue / total_orders if total_orders > 0 else 0
        } 
