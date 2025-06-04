from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from base.models import OrderModel, OrderItem, ProductModel
from api.serializers import OrderModelSerializer, OrderItemSerializer
from django.db.models import Sum
from base.managers import ShipmentManager

from api.permissions import HasRolePermission
from base.enums.role import ROLE

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderModelSerializer
    queryset = OrderModel.objects.all()

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return OrderModel.objects.none()
        if hasattr(user, 'role') and user.role == 'admin':
            return OrderModel.objects.all()
        return OrderModel.objects.filter(user=user)

    def create(self, request):
        """
        Create a new order and automatically create a shipment for it.
        Expected payload:
        {
            "items": [
                {"product": "product_id", "quantity": 2},
                {"product": "another_product_id", "quantity": 1}
            ]
        }
        """
        user = request.user
        if not user.is_authenticated:
            return Response(
                {"error": "Authentication required"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        items_data = request.data.get('items', [])
        if not items_data:
            return Response(
                {"error": "Order must contain at least one item"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # Create the order
                order = OrderModel.objects.create(user=user)
                
                # Create order items
                for item_data in items_data:
                    product_id = item_data.get('product')
                    quantity = item_data.get('quantity', 1)
                    
                    try:
                        product = ProductModel.objects.get(id=product_id)
                        
                        # Check stock availability
                        if product.stock < quantity:
                            return Response(
                                {"error": f"Insufficient stock for {product.name}. Available: {product.stock}, Requested: {quantity}"}, 
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        
                        # Create order item
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity,
                            price=product.price
                        )
                        
                        # Update product stock
                        product.stock -= quantity
                        product.save()
                        
                    except ProductModel.DoesNotExist:
                        return Response(
                            {"error": f"Product with id {product_id} does not exist"}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                # Create shipment using ShipmentManager
                shipment_manager = ShipmentManager()
                shipment = shipment_manager.create_shipment(order)
                
                # Update order status to indicate shipment created
                order.status = "shipped"
                order.save()
                
                serializer = OrderModelSerializer(order)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {"error": f"Failed to create order: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='analytics')
    def analytics(self, request):
        """
        Returns basic sales analytics data for the admin dashboard.
        """
        if not HasRolePermission([ROLE.ADMIN]).has_permission(request, self):
            raise PermissionDenied("Only admin users can view all users")

        total_orders = OrderModel.objects.count()
        # Assume your OrderModel has a .total field, or calculate sum of items
        total_sales = sum(
            sum(item.price * item.quantity for item in order.items.all())
            for order in OrderModel.objects.all()
        )

        # Top products by quantity sold
        top_products = (
            OrderItem.objects
                .values('product__name')
                .annotate(total_sold=Sum('quantity'))
                .order_by('-total_sold')[:5]
        )

        return Response({
            "total_orders": total_orders,
            "total_sales": total_sales,
            "top_products": list(top_products),
        })

    @action(detail=True, methods=['get'], url_path='track')
    def track_shipment(self, request, pk=None):
        """
        Track the shipment for a specific order.
        GET /api/order/{order_id}/track/
        """
        order = self.get_object()
        
        # Check if user can access this order
        if order.user != request.user and not (hasattr(request.user, 'role') and request.user.role == 'admin'):
            raise PermissionDenied("You can only track your own orders")
        
        if hasattr(order, 'shipment'):
            shipment_manager = ShipmentManager()
            tracking_info = shipment_manager.get_shipment_status(order.shipment.tracking_number)
            return Response(tracking_info)
        else:
            return Response(
                {"error": "No shipment found for this order"}, 
                status=status.HTTP_404_NOT_FOUND
            )
