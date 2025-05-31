from rest_framework import serializers
from base.models import *

class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ["id", "username", "email", "firstName", "lastName", "phone", "role"]
        read_only_fields = ["id", "role"]

class ProductModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = ["id", "name", "description", "price", "created_at", "updated_at"]
