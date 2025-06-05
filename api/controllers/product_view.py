from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from api.permissions import HasRolePermission
from base.enums.role import ROLE
from rest_framework.exceptions import PermissionDenied

from base.models import ProductModel, CategoryModel
from api.serializers import ProductModelSerializer

class ProductViewSet(viewsets.ViewSet):
    def list(self, request):
        """
        GET /api/product/
        Optional query params:
        - categories (comma‑separated strings) e.g. ?categories=cat1,cat2
        - include_inactive (boolean) e.g. ?include_inactive=true (admin only)

        If categories is provided, returns products linked to those categories.
        By default, only returns active products unless include_inactive=true and user is admin.
        """
        querySet = ProductModel.objects.all()

        # Handle include_inactive parameter (admin only)
        include_inactive = request.query_params.get("include_inactive", "false").lower() == "true"
        if not include_inactive:
            querySet = querySet.filter(is_active=True)
        elif include_inactive and not HasRolePermission([ROLE.ADMIN]).has_permission(request, self):
            # Non-admin users cannot see inactive products
            querySet = querySet.filter(is_active=True)

        categoriesParam = request.query_params.get("categories")
        if categoriesParam:
            categoryIds = [c.strip() for c in categoriesParam.split(",") if c.strip()]
            valid_category_ids = []
            for cat_id in categoryIds:
                try:
                    CategoryModel.objects.get(id=cat_id)  # Just validate the category exists
                    valid_category_ids.append(cat_id)
                except CategoryModel.DoesNotExist:
                    pass  # Ignore invalid categories
            
            if valid_category_ids:
                querySet = querySet.filter(category__in=valid_category_ids)
            else:
                querySet = querySet.none()

        serializer = ProductModelSerializer(querySet, many=True)
        return Response(serializer.data)
  
    def retrieve(self, request, pk=None):
        """
        GET /api/product/{id}/
        Returns a specific product by ID.
        """
        product = get_object_or_404(ProductModel, pk=pk)
        serializer = ProductModelSerializer(product)
        return Response(serializer.data)

    def create(self, request):
        if not HasRolePermission([ROLE.ADMIN]).has_permission(request, self):
            raise PermissionDenied("Only admin users can create products")
            
        serializer = ProductModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        if not HasRolePermission([ROLE.ADMIN]).has_permission(request, self):
            raise PermissionDenied("Only admin users can update products")
            
        product = get_object_or_404(ProductModel, pk=pk)
        serializer = ProductModelSerializer(product, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='enable')
    def enable_product(self, request, pk=None):
        """
        POST /api/product/{id}/enable/
        Enable a product (set is_active=True). Admin only.
        """
        if not HasRolePermission([ROLE.ADMIN]).has_permission(request, self):
            raise PermissionDenied("Only admin users can enable products")
            
        product = get_object_or_404(ProductModel, pk=pk)
        product.is_active = True
        product.save()
        
        serializer = ProductModelSerializer(product)
        return Response({
            "message": f"Product '{product.name}' has been enabled",
            "product": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='disable')
    def disable_product(self, request, pk=None):
        """
        POST /api/product/{id}/disable/
        Disable a product (set is_active=False). Admin only.
        """
        if not HasRolePermission([ROLE.ADMIN]).has_permission(request, self):
            raise PermissionDenied("Only admin users can disable products")
            
        product = get_object_or_404(ProductModel, pk=pk)
        product.is_active = False
        product.save()
        
        serializer = ProductModelSerializer(product)
        return Response({
            "message": f"Product '{product.name}' has been disabled",
            "product": serializer.data
        }, status=status.HTTP_200_OK)
