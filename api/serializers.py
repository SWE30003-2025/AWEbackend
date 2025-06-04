from rest_framework import serializers
from base.models import *

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    class Meta:
        model = OrderItem
        fields = ['product', 'product_name', 'quantity', 'price']
        # You may include 'product' (as ID) and 'product_name' (as read-only)

class OrderModelSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()

    class Meta:
        model = OrderModel
        fields = ['id', 'user', 'created_at', 'status', 'total', 'items']

    def get_total(self, obj):
        return obj.total


class UserModelSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = UserModel
        fields = ["id", "username", "email", "firstName", "lastName", "phone", "role", "password"]
        read_only_fields = ["id", "role", "username", "email"]

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
