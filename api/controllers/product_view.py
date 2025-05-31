from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from api.permissions import HasRolePermission
from base.enums.role import ROLE
from rest_framework.exceptions import PermissionDenied

from base.models import ProductModel
from api.serializers import ProductModelSerializer

class ProductViewSet(viewsets.ViewSet):
    def list(self, request):
        products = ProductModel.objects.all()
        serializer = ProductModelSerializer(products, many=True)
        return Response(serializer.data)
  
    def retrieve(self, request, pk=None):
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

    def destroy(self, request, pk=None):
        if not HasRolePermission([ROLE.ADMIN]).has_permission(request, self):
            raise PermissionDenied("Only admin users can delete products")
            
        product = get_object_or_404(ProductModel, pk=pk)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
