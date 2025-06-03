from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from base.models import OrderModel, OrderItem
from api.serializers import OrderModelSerializer
from django.db.models import Sum

from api.permissions import HasRolePermission
from base.enums.role import ROLE

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderModelSerializer
    queryset = OrderModel.objects.all()

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return OrderModel.objects.none()
        if hasattr(user, 'role') and user.role == 'admin':
            return OrderModel.objects.all()
        return OrderModel.objects.filter(user=user)

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
