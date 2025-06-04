from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from base.models import ShoppingCartModel, CartItemModel, ProductModel, OrderModel, OrderItem
from api.serializers import ShoppingCartModelSerializer, CartItemModelSerializer, OrderModelSerializer
from api.permissions import HasRolePermission, get_authenticated_user
from base.managers import ShipmentManager
from base.enums.role import ROLE

class ShoppingCartViewSet(viewsets.ViewSet):
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [HasRolePermission([ROLE.CUSTOMER])]

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

    def put(self, request):
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

    def delete(self, request):
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

    @action(detail=False, methods=['post'], url_path='place-order')
    def place_order(self, request):
        """
        Place an order from cart items
        POST /api/shopping-cart/place-order/
        Body: {
            "shipping_full_name": "John Smith",
            "shipping_address": "123 Main St",
            "shipping_city": "Melbourne",
            "shipping_postal_code": "3000"
        }
        """
        user = get_authenticated_user(request)
        cart = self._get_or_create_cart(user)
        
        # Check if cart has items
        if not cart.items.exists():
            return Response(
                {"error": "Cart is empty"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get shipping information
        shipping_full_name = request.data.get('shipping_full_name')
        shipping_address = request.data.get('shipping_address')
        shipping_city = request.data.get('shipping_city')
        shipping_postal_code = request.data.get('shipping_postal_code')
        
        if not all([shipping_full_name, shipping_address, shipping_city, shipping_postal_code]):
            return Response(
                {"error": "All shipping fields are required: shipping_full_name, shipping_address, shipping_city, shipping_postal_code"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                total_amount = cart.total
                
                if user.wallet < total_amount:
                    return Response(
                        {"error": f"Insufficient wallet balance. Required: ${total_amount}, Available: ${user.wallet}"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                order = OrderModel.objects.create(
                    user=user,
                    shipping_full_name=shipping_full_name,
                    shipping_address=shipping_address,
                    shipping_city=shipping_city,
                    shipping_postal_code=shipping_postal_code
                )
                
                # Create order items from cart items
                for cart_item in cart.items.all():
                    if cart_item.product.stock < cart_item.quantity:
                        return Response(
                            {"error": f"Insufficient stock for {cart_item.product.name}. Available: {cart_item.product.stock}, Requested: {cart_item.quantity}"}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price  # Current price at time of order
                    )
                    
                    # Update product stock
                    cart_item.product.stock -= cart_item.quantity
                    cart_item.product.save()
                
                user.wallet -= total_amount
                user.save()
                
                shipment_manager = ShipmentManager()
                shipment_manager.create_shipment(order)
                
                cart.clear()
                
                serializer = OrderModelSerializer(order)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {"error": f"Failed to place order: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 
