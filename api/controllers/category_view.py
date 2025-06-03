from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from api.permissions import HasRolePermission
from base.enums.role import ROLE
from rest_framework.exceptions import PermissionDenied

from base.models import CategoryModel
from api.serializers import CategoryModelSerializer

class CategoryViewSet(viewsets.ViewSet):
    def list(self, request):
        """
        GET /api/categories/
        Returns all categories as a flat list.
        """
        queryset = CategoryModel.objects.all().order_by('name')
        serializer = CategoryModelSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """
        GET /api/categories/{id}/
        Returns a specific category by ID.
        """
        category = get_object_or_404(CategoryModel, pk=pk)
        serializer = CategoryModelSerializer(category)
        return Response(serializer.data)
    
    def create(self, request):
        """
        POST /api/categories/
        Create a new category. Admin only.
        """
        if not HasRolePermission([ROLE.ADMIN]).has_permission(request, self):
            raise PermissionDenied("Only admin users can create categories")
            
        serializer = CategoryModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """
        PUT /api/categories/{id}/
        Update a category. Admin only.
        """
        if not HasRolePermission([ROLE.ADMIN]).has_permission(request, self):
            raise PermissionDenied("Only admin users can update categories")
            
        category = get_object_or_404(CategoryModel, pk=pk)
        serializer = CategoryModelSerializer(category, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """
        DELETE /api/categories/{id}/
        Delete a category. Admin only.
        """
        if not HasRolePermission([ROLE.ADMIN]).has_permission(request, self):
            raise PermissionDenied("Only admin users can delete categories")
            
        category = get_object_or_404(CategoryModel, pk=pk)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 
