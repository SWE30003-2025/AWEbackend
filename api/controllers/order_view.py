from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from base.models import OrderModel, InvoiceModel
from base.enums import ROLE
from base.managers import StatisticsManager

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

        period = request.query_params.get("period", "month")
        start_date = request.query_params.get("start_date", None)
        end_date = request.query_params.get("end_date", None)

        stats_manager = StatisticsManager()

        sales_by_period = stats_manager.get_sales_by_period(
            period_type=period,
            start_date=start_date,
            end_date=end_date
        )

        top_products = stats_manager.get_top_selling_products(
            start_date=start_date,
            end_date=end_date,
            limit=5
        )

        summary = stats_manager.get_sales_summary(
            start_date=start_date,
            end_date=end_date
        )

        return Response({
            "summary": summary,
            "sales_by_period": list(sales_by_period),
            "top_products": list(top_products)
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
