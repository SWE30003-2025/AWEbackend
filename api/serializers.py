from rest_framework import serializers
from base.models import *
from base.enums.role import ROLE

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    class Meta:
        model = OrderItem
        fields = ['product', 'product_name', 'quantity', 'price']
        # You may include 'product' (as ID) and 'product_name' (as read-only)

class ShipmentModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentModel
        fields = [
            'id', 'tracking_number', 'status', 'carrier', 
            'estimated_delivery', 'actual_delivery', 'created_at', 
            'updated_at'
        ]

class OrderModelSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    shipment = ShipmentModelSerializer(read_only=True)

    class Meta:
        model = OrderModel
        fields = [
            'id', 'user', 'created_at', 'status', 'total', 'items', 'shipment',
            'shipping_full_name', 'shipping_address', 'shipping_city', 'shipping_postal_code'
        ]

    def get_total(self, obj):
        return obj.total

class UserModelSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    wallet = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    class Meta:
        model = UserModel
        fields = ["id", "username", "email", "firstName", "lastName", "phone", "role", "password", "wallet"]
        read_only_fields = ["id", "role", "username", "email"]

    def to_representation(self, instance):
        """Customize the representation to only include wallet for customers"""
        data = super().to_representation(instance)
        
        # Only include wallet for customers
        if instance.role != ROLE.CUSTOMER.value:
            data.pop('wallet', None)
        
        return data

    def validate_wallet(self, value):
        """Validate wallet field"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Wallet balance cannot be negative")
        return value

    def validate(self, attrs):
        """Validate that only customers can modify wallet"""
        wallet = attrs.get('wallet')
        
        # If updating an existing instance
        if self.instance:
            # Only allow wallet updates for customers
            if wallet is not None and self.instance.role != ROLE.CUSTOMER.value:
                raise serializers.ValidationError(
                    {"wallet": "Wallet feature is only available for customers"}
                )
        
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = UserModel(**validated_data)
        user.set_password(password)
        user.save()
        return user

class CategoryModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryModel
        fields = ["id", "name", "description"]

class ProductModelSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name', read_only=True)
    category_id = serializers.CharField(write_only=True, source='category', allow_null=True, required=False)
    
    class Meta:
        model = ProductModel
        fields = ["id", "name", "description", "price", "stock", "category", "category_id"]

class CartItemModelSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_price = serializers.DecimalField(source="product.price", max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItemModel
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'subtotal']
        read_only_fields = ['id']

    def get_subtotal(self, obj):
        return obj.subtotal

    def validate_quantity(self, value):
        """Validate that quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value

class ShoppingCartModelSerializer(serializers.ModelSerializer):
    items = CartItemModelSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    
    class Meta:
        model = ShoppingCartModel
        fields = ['id', 'user', 'total', 'total_items', 'items']
        read_only_fields = ['id', 'user']

    def get_total(self, obj):
        return obj.total

    def get_total_items(self, obj):
        return obj.total_items
