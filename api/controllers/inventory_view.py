from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from base.managers import InventoryManager
from base.models.product_model import ProductModel
from api.permissions import HasRolePermission
from base.enums.role import ROLE
from api.serializers import ProductModelSerializer

class InventoryViewSet(viewsets.ViewSet):
    @action(detail=True, methods=["post"])
    def update_stock(self, request, pk=None):
        # Permission check: inventory managers and admins
        if not HasRolePermission([ROLE.INVENTORY_MANAGER, ROLE.ADMIN]).has_permission(request, self):
            raise PermissionDenied("Only inventory managers and admins can update stock.")
        
        product = get_object_or_404(ProductModel, pk=pk)
        manager = InventoryManager()

        if "amount" in request.data:
            try:
                amount = int(request.data["amount"])
            except ValueError:
                return Response({"error": "Amount must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
            new_stock = manager.adjust_stock(product.id, amount)
            action_type = "adjusted"
        else:
            return Response({"error": "Provide amount to adjust stock."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProductModelSerializer(product)
        return Response({
            "message": f"Stock {action_type}.",
            "product": serializer.data,
            "new_stock": new_stock,
        }, status=status.HTTP_200_OK)
