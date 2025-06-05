from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from base.models import ShipmentModel
from base.managers import ShipmentManager
from base.enums import ROLE, SHIPMENT_STATUS

from api.permissions import HasRolePermission, get_authenticated_user
from api.serializers import ShipmentModelSerializer

class ShipmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ShipmentModelSerializer
    queryset = ShipmentModel.objects.all()

    def get_queryset(self):
        user = get_authenticated_user(self.request)
        if not user:
            return ShipmentModel.objects.none()
        
        if HasRolePermission([ROLE.ADMIN, ROLE.SHIPMENT_MANAGER]).has_permission(self.request, self):
            return ShipmentModel.objects.all()
        
        return ShipmentModel.objects.filter(order__user=user)

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        Update the status of a shipment (for shipment managers and admins only).
        POST /api/shipment/{id}/update-status/
        Body: {"status": "new_status"}
        
        Available statuses:
        - pending
        - processing
        - shipped
        - in_transit
        - out_for_delivery
        - delivered
        - failed
        """
        permission_check = HasRolePermission([ROLE.ADMIN, ROLE.SHIPMENT_MANAGER])
        if not permission_check.has_permission(request, self):
            raise PermissionDenied("Only shipment managers and admins can update shipment status")

        shipment = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {"error": "Status field is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_statuses = [status.value for status in SHIPMENT_STATUS]
        if new_status not in valid_statuses:
            return Response(
                {
                    "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}", 
                    "valid_statuses": valid_statuses
                }, 
                status=status.HTTP_400_BAD_REQUEST
            )

        current_status = shipment.status
        if current_status == SHIPMENT_STATUS.DELIVERED.value and new_status != SHIPMENT_STATUS.FAILED.value:
            return Response(
                {"error": "Cannot change status of a delivered shipment (except to failed)"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if current_status == SHIPMENT_STATUS.FAILED.value:
            return Response(
                {"error": "Cannot update status of a failed shipment"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        shipment_manager = ShipmentManager()
        shipment_manager.update_shipment_status(shipment.id, new_status)
        
        shipment.refresh_from_db()
        serializer = ShipmentModelSerializer(shipment)
        
        return Response({
            "message": f"Shipment status updated successfully from {current_status} to {new_status}",
            "shipment": serializer.data
        })

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """
        Shipment dashboard with statistics (for shipment managers and admins only).
        GET /api/shipment/dashboard/
        """
        permission_check = HasRolePermission([ROLE.ADMIN, ROLE.SHIPMENT_MANAGER])
        if not permission_check.has_permission(request, self):
            raise PermissionDenied("Only shipment managers and admins can view the dashboard")

        total_shipments = ShipmentModel.objects.count()
        
        status_counts = {}
        for shipment in ShipmentModel.objects.all():
            status = shipment.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        recent_shipments = ShipmentModel.objects.order_by('-created_at')[:10]
        recent_serializer = ShipmentModelSerializer(recent_shipments, many=True)
        
        # Calculate average delivery time for completed shipments
        delivered_shipments = ShipmentModel.objects.filter(
            status=SHIPMENT_STATUS.DELIVERED.value,
            actual_delivery__isnull=False
        )
        
        avg_delivery_time = None
        if delivered_shipments.exists():
            total_delivery_time = sum(
                (shipment.actual_delivery - shipment.created_at).total_seconds()
                for shipment in delivered_shipments
            )
            avg_delivery_time = total_delivery_time / delivered_shipments.count() / 86400 
        
        return Response({
            "total_shipments": total_shipments,
            "status_counts": status_counts,
            "recent_shipments": recent_serializer.data,
            "avg_delivery_time_days": round(avg_delivery_time, 2) if avg_delivery_time else None,
            "valid_statuses": [status.value for status in SHIPMENT_STATUS]
        }) 
