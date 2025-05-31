from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from base.models import UserModel
from api.serializers import UserModelSerializer

class UserViewSet(viewsets.ViewSet):
    def list(self, request):
        """
        Retrieve all UserModel records.
        GET /api/user
        """
        users = UserModel.objects.all()
        serializer = UserModelSerializer(users, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """
        Retrieve a specific UserModel record.
        GET /api/user/{pk}
        """
        user = get_object_or_404(UserModel, pk=pk)
        
        # Check if user is accessing their own data
        if str(request.user.id) != str(pk):
            raise PermissionDenied("You can only view your own profile")
            
        serializer = UserModelSerializer(user)
        return Response(serializer.data)

    def create(self, request):
        """
        Create a new UserModel record.
        POST /api/user
        """
        serializer = UserModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """
        Update a UserModel record.
        PUT /api/user/{pk}
        """
        user = get_object_or_404(UserModel, pk=pk)
        
        # Check if user is updating their own data
        if str(request.user.id) != str(pk):
            raise PermissionDenied("You can only update your own profile")
        
        serializer = UserModelSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    