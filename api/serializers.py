from rest_framework import serializers
from base.models import UserModel, ProductModel

class UserModelSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)  # Password is optional for update

    class Meta:
        model = UserModel
        fields = ["id", "username", "email", "firstName", "lastName", "phone", "role", "password"]
        read_only_fields = ["id", "role", "username", "email"]  # Can't change username/email here

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
        print(f"[REGISTER] password repr: {repr(password)}")
        user = UserModel(**validated_data)
        user.set_password(password)
        print(f"[REGISTER] Password after hashing: {user.password}")
        user.save()
        return user


class ProductModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = ["id", "name", "description", "price", "stock", "created_at", "updated_at"]
