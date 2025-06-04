from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from base.models import ShoppingCartModel, CartItemModel, ProductModel
from api.serializers import ShoppingCartModelSerializer, CartItemModelSerializer
from api.permissions import HasRolePermission, get_authenticated_user
from base.enums.role import ROLE

class ShoppingCartViewSet(viewsets.ViewSet):
    permission_classes = [HasRolePermission([ROLE.CUSTOMER])]

    def _get_or_create_cart(self, user):
        """Get or create a shopping cart for the user"""
        cart, created = ShoppingCartModel.objects.get_or_create(user=user)
        return cart

    def list(self, request):
        """
        Get the current user's shopping cart
        GET /api/shopping-cart/
        """
        user = get_authenticated_user(request)
        cart = self._get_or_create_cart(user)
        serializer = ShoppingCartModelSerializer(cart)
        return Response(serializer.data)

    def create(self, request):
        """
        Add an item to the shopping cart
        POST /api/shopping-cart/
        Body: {"product_id": "uuid", "quantity": 1}
        """
        user = get_authenticated_user(request)
        
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        if not product_id:
            return Response(
                {"error": "product_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response(
                    {"error": "quantity must be greater than 0"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {"error": "quantity must be a valid number"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cart = self._get_or_create_cart(user)
            product = ProductModel.objects.get(pk=product_id)
            
            # Check if item already exists in cart
            cart_item, created = CartItemModel.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                # Item already exists, update quantity
                cart_item.quantity += quantity
                cart_item.save()
            
            serializer = CartItemModelSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ProductModel.DoesNotExist:
            return Response(
                {"error": f"Product with id {product_id} does not exist"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, pk=None):
        """
        Update the quantity of an item in the cart
        PUT /api/shopping-cart/
        Body: {"product_id": "uuid", "quantity": 2}
        """
        user = get_authenticated_user(request)
        
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')
        
        if not product_id or quantity is None:
            return Response(
                {"error": "product_id and quantity are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            quantity = int(quantity)
            if quantity < 0:
                return Response(
                    {"error": "quantity cannot be negative"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {"error": "quantity must be a valid number"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cart = self._get_or_create_cart(user)
            cart_item = CartItemModel.objects.get(cart=cart, product_id=product_id)
            
            if quantity <= 0:
                cart_item.delete()
                return Response(
                    {"message": "Item removed from cart"}, 
                    status=status.HTTP_200_OK
                )
            else:
                cart_item.quantity = quantity
                cart_item.save()
                serializer = CartItemModelSerializer(cart_item)
                return Response(serializer.data)
        except CartItemModel.DoesNotExist:
            return Response(
                {"error": f"Product with id {product_id} not found in cart"}, 
                status=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, pk=None):
        """
        Remove an item from the cart
        DELETE /api/shopping-cart/
        Body: {"product_id": "uuid"}
        """
        user = get_authenticated_user(request)
        cart = self._get_or_create_cart(user)
        
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response(
                {"error": "product_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cart_item = CartItemModel.objects.get(cart=cart, product_id=product_id)
            cart_item.delete()
            return Response(
                {"message": "Item removed from cart"}, 
                status=status.HTTP_200_OK
            )
        except CartItemModel.DoesNotExist:
            return Response(
                {"error": "Item not found in cart"}, 
                status=status.HTTP_404_NOT_FOUND
            ) 