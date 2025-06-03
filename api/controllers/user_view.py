from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from api.permissions import HasRolePermission
from base.enums.role import ROLE

from base.models import UserModel
from api.serializers import UserModelSerializer

class UserViewSet(viewsets.ViewSet):
    def list(self, request):
        """
        Retrieve all UserModel records.
        GET /api/user
        Admin only.
        """
        if not HasRolePermission([ROLE.ADMIN]).has_permission(request, self):
            raise PermissionDenied("Only admin users can view all users")
            
        users = UserModel.objects.all()
        serializer = UserModelSerializer(users, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """
        Retrieve a specific UserModel record.
        GET /api/user/{pk}
        Users can only view their own profile.
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
        Admin only.
        """
        if not HasRolePermission([ROLE.ADMIN]).has_permission(request, self):
            raise PermissionDenied("Only admin users can create new users")
            
        serializer = UserModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """
        Update a UserModel record.
        PUT /api/user/{pk}
        Users can only update their own profile.
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

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        """
        Login endpoint.
        POST /api/user/login/
        """
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Please provide both username and password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = UserModel.objects.get(username=username)
            # Raw password comparison - consistent with get_authenticated_user
            if user.password == password:
                serializer = UserModelSerializer(user)
                return Response({"user": serializer.data})
            else:
                return Response(
                    {"error": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except UserModel.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def signup(self, request):
        print("HIT SIGNUP ENDPOINT!")
        """
        Signup endpoint.
        POST /api/user/signup
        """
        # Set default role as customer for new signups
        request.data["role"] = ROLE.CUSTOMER.value
        
        serializer = UserModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
