from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from api.permissions import HasRolePermission, get_authenticated_user
from api.serializers import UserModelSerializer

from base.enums import ROLE
from base.models import UserModel

class UserViewSet(viewsets.ViewSet):
    def get_permissions(self):
        if self.action in ["login", "signup"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]
    
    def retrieve(self, request, pk=None):
        """
        Retrieve a specific UserModel record.
        GET /api/user/{pk}
        Users can only view their own profile.
        """
        user = get_object_or_404(UserModel, pk=pk)
        
        # Check if user is accessing their own data
        current_user = get_authenticated_user(request)
        if not current_user:
            raise PermissionDenied("Authentication required")
            
        if str(current_user.id) != str(pk):
            raise PermissionDenied("You can only view your own profile")
            
        serializer = UserModelSerializer(user)
        return Response(serializer.data)

    def update(self, request, pk=None):
        """
        Update a UserModel record.
        PUT /api/user/{pk}
        Users can only update their own profile.
        For customers, wallet field can be updated.
        """
        user = get_object_or_404(UserModel, pk=pk)
        
        # Check if user is updating their own data
        current_user = get_authenticated_user(request)
        if not current_user:
            raise PermissionDenied("Authentication required")
        
        if str(current_user.id) != str(pk):
            raise PermissionDenied("You can only update your own profile")
        
        serializer = UserModelSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
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

    @action(detail=False, methods=["post"])
    def signup(self, request):
        """
        Signup endpoint.
        POST /api/user/signup/
        """
        # Set default role as customer for new signups
        request.data["role"] = ROLE.CUSTOMER.value
        
        user_data = request.data.copy()
        password = user_data.get("password")
        
        if not password:
            return Response(
                {"error": "Password is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = UserModel.objects.create(
                username=user_data.get("username"),
                email=user_data.get("email"),
                firstName=user_data.get("firstName"),
                lastName=user_data.get("lastName"),
                phone=user_data.get("phone", ""),
                password=password,
                role=ROLE.CUSTOMER.value,
                wallet=0.00
            )
            
            serializer = UserModelSerializer(user)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to create user: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
