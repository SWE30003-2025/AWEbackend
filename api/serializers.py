from rest_framework import serializers
from base.models import *
from base.enums.role import ROLE

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    class Meta:
        model = OrderItemModel
        fields = ['product', 'product_name', 'quantity', 'price']

class ShipmentModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentModel
        fields = [
            'id', 'tracking_number', 'status', 'carrier', 
            'estimated_delivery', 'actual_delivery', 'created_at', 
            'updated_at', "order_id"
        ]
        
class InvoiceModelSerializer(serializers.ModelSerializer):
    receipts = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceModel
        fields = ['id', 'invoice_number', 'amount_due', 'status', 'due_date', 'created_at', 'receipts']

    def get_receipts(self, obj):
        # An invoice can have multiple payments (though current logic implies one)
        # Each payment has one receipt
        receipt_data = []
        for payment in obj.payments.all(): # obj is an InvoiceModel instance
            if hasattr(payment, 'receipt') and payment.receipt:
                serializer = ReceiptModelSerializer(payment.receipt)
                receipt_data.append(serializer.data)
        return receipt_data

class ReceiptModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptModel
        fields = ['id', 'receipt_number', 'amount_paid', 'created_at']

class OrderModelSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    shipment = ShipmentModelSerializer(read_only=True, allow_null=True)

    class Meta:
        model = OrderModel
        fields = [
            'id', 'user', 'created_at', 'status', 'payment_status',
            'total', 'items', 'shipment', 'invoice',
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
    category_id = serializers.CharField(write_only=True, allow_null=True, required=False)
    
    class Meta:
        model = ProductModel
        fields = ["id", "name", "description", "price", "stock", "category", "category_id", "is_active"]
    
    def create(self, validated_data):
        category_id = validated_data.pop('category_id', None)
        if category_id:
            try:
                # Try to get category by ID first
                category = CategoryModel.objects.get(id=category_id)
                validated_data['category'] = category
            except CategoryModel.DoesNotExist:
                # If that fails, try to get by name
                try:
                    category = CategoryModel.objects.get(name=category_id)
                    validated_data['category'] = category
                except CategoryModel.DoesNotExist:
                    raise serializers.ValidationError(f"Category '{category_id}' not found")
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        category_id = validated_data.pop('category_id', None)
        if category_id:
            try:
                # Try to get category by ID first
                category = CategoryModel.objects.get(id=category_id)
                validated_data['category'] = category
            except CategoryModel.DoesNotExist:
                # If that fails, try to get by name
                try:
                    category = CategoryModel.objects.get(name=category_id)
                    validated_data['category'] = category
                except CategoryModel.DoesNotExist:
                    raise serializers.ValidationError(f"Category '{category_id}' not found")
        return super().update(instance, validated_data)

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
