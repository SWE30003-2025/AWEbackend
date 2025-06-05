from django.db.models import Sum

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from base.models import OrderModel, OrderItemModel, InvoiceModel
from base.enums import ROLE
from base.managers import ShipmentManager

from api.serializers import InvoiceModelSerializer, OrderModelSerializer
from api.permissions import HasRolePermission, get_authenticated_user

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderModelSerializer
    queryset = OrderModel.objects.all()

    def get_queryset(self):
        user = get_authenticated_user(self.request)
        if not user:
            return OrderModel.objects.none()
        
        # Admins can see all orders
        if HasRolePermission([ROLE.ADMIN]).has_permission(self.request, self):
            return OrderModel.objects.all()
        
        # Customers can only see their own orders
        return OrderModel.objects.filter(user=user)

    @action(detail=False, methods=["get"], url_path="analytics")
    def analytics(self, request):
        if not HasRolePermission([ROLE.ADMIN, ROLE.STATISTICS_MANAGER]).has_permission(request, self):
            raise PermissionDenied("Only admin and statistics manager users can view analytics")

        total_orders = OrderModel.objects.count()
        total_sales = sum(
            sum(item.price * item.quantity for item in order.items.all())
            for order in OrderModel.objects.all()
        )

        top_products = (
            OrderItemModel.objects
                .values("product__name")
                .annotate(total_sold=Sum("quantity"))
                .order_by("-total_sold")[:5]
        )

        return Response({
            "total_orders": total_orders,
            "total_sales": total_sales,
            "top_products": list(top_products),
        })

    @action(detail=True, methods=["get"], url_path="invoice")
    def retrieve_invoice(self, request, pk=None):
        """
        Retrieve the invoice for a specific order.
        GET /api/order/{order_id}/invoice/
        """
        order = self.get_object()
        
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
            return Response(
                {"error": "An error occurred while retrieving the invoice."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
