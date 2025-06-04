from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from base.models import ShipmentModel
from api.serializers import ShipmentModelSerializer
from base.managers import ShipmentManager
from api.permissions import HasRolePermission, get_authenticated_user
from base.enums.role import ROLE

class ShipmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ShipmentModelSerializer
    queryset = ShipmentModel.objects.all()

    def get_queryset(self):
        user = get_authenticated_user(self.request)
        if not user:
            return ShipmentModel.objects.none()
        
        # Admins and shipment managers can see all shipments
        if hasattr(user, 'role') and user.role in [ROLE.ADMIN.value, ROLE.SHIPMENT_MANAGER.value]:
            return ShipmentModel.objects.all()
        
        # Customers can only see their own shipments
        return ShipmentModel.objects.filter(order__user=user)

    @action(detail=False, methods=['get'], url_path='track')
    def track_by_number(self, request):
        """
        Track a shipment by tracking number.
        GET /api/shipment/track/?tracking_number=XXXXX
        """
        tracking_number = request.query_params.get('tracking_number')
        
        if not tracking_number:
            return Response(
                {"error": "tracking_number query parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        shipment_manager = ShipmentManager()
        tracking_info = shipment_manager.get_shipment_status(tracking_number)
        
        if tracking_info:
            # Check if user can access this shipment
            user = get_authenticated_user(request)
            try:
                shipment = ShipmentModel.objects.get(tracking_number=tracking_number)
                if (shipment.order.user != user and 
                    not (hasattr(user, 'role') and user.role in [ROLE.ADMIN.value, ROLE.SHIPMENT_MANAGER.value])):
                    raise PermissionDenied("You can only track your own shipments")
            except ShipmentModel.DoesNotExist:
                pass
            
            return Response(tracking_info)
        else:
            return Response(
                {"error": "Tracking number not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        Update the status of a shipment (for shipment managers and admins only).
        POST /api/shipment/{id}/update-status/
        Body: {"status": "new_status"}
        """
        # Check permissions using HasRolePermission
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

        shipment_manager = ShipmentManager()
        shipment_manager.update_shipment_status(shipment.id, new_status)
        
        # Refresh from database
        shipment.refresh_from_db()
        serializer = ShipmentModelSerializer(shipment)
        
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """
        Shipment dashboard with statistics (for shipment managers and admins only).
        GET /api/shipment/dashboard/
        """
        # Check permissions using HasRolePermission
        permission_check = HasRolePermission([ROLE.ADMIN, ROLE.SHIPMENT_MANAGER])
        if not permission_check.has_permission(request, self):
            raise PermissionDenied("Only shipment managers and admins can view the dashboard")

        # Get statistics
        total_shipments = ShipmentModel.objects.count()
        
        # Count by status
        status_counts = {}
        for shipment in ShipmentModel.objects.all():
            status = shipment.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Recent shipments
        recent_shipments = ShipmentModel.objects.order_by('-created_at')[:10]
        recent_serializer = ShipmentModelSerializer(recent_shipments, many=True)
        
        return Response({
            "total_shipments": total_shipments,
            "status_counts": status_counts,
            "recent_shipments": recent_serializer.data
        }) 
