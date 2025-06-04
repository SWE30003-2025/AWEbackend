from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from base.models import OrderModel, OrderItemModel, InvoiceModel
from api.serializers import OrderModelSerializer, OrderItemSerializer, InvoiceModelSerializer
from django.db.models import Sum
from base.managers import ShipmentManager

from api.permissions import HasRolePermission, get_authenticated_user
from base.enums.role import ROLE

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderModelSerializer
    queryset = OrderModel.objects.all()

    def get_queryset(self):
        user = get_authenticated_user(self.request)
        if not user:
            return OrderModel.objects.none()
        
        # Admins can see all orders
        if hasattr(user, 'role') and user.role == ROLE.ADMIN.value:
            return OrderModel.objects.all()
        
        # Customers can only see their own orders
        return OrderModel.objects.filter(user=user)

    @action(detail=False, methods=['get'], url_path='analytics')
    def analytics(self, request):
        """
        Returns basic sales analytics data for the admin dashboard.
        """
        # Check permissions using HasRolePermission
        permission_check = HasRolePermission([ROLE.ADMIN])
        if not permission_check.has_permission(request, self):
            raise PermissionDenied("Only admin users can view analytics")

        total_orders = OrderModel.objects.count()
        # Calculate total sales
        total_sales = sum(
            sum(item.price * item.quantity for item in order.items.all())
            for order in OrderModel.objects.all()
        )

        # Top products by quantity sold
        top_products = (
            OrderItemModel.objects
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
        user = get_authenticated_user(request)
        
        # Check if user can access this order
        if (order.user != user and 
            not (hasattr(user, 'role') and user.role in [ROLE.ADMIN.value, ROLE.SHIPMENT_MANAGER.value])):
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

    @action(detail=True, methods=['get'], url_path='invoice')
    def retrieve_invoice(self, request, pk=None):
        """
        Retrieve the invoice for a specific order.
        GET /api/order/{order_id}/invoice/
        """
        order = self.get_object() # This already filters based on get_queryset
        
        try:
            invoice = InvoiceModel.objects.get(order=order)
            serializer = InvoiceModelSerializer(invoice)
            return Response(serializer.data)
        except InvoiceModel.DoesNotExist:
            return Response(
                {"error": "Invoice not found for this order"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Log the exception e
            return Response(
                {"error": "An error occurred while retrieving the invoice."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
